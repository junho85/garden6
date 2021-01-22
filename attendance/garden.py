from datetime import date, timedelta, datetime
import pymongo
import pprint
from attendance.slack_tools import SlackTools
from attendance.mongo_tools import MongoTools
from attendance.config_tools import ConfigTools


class Garden:
    def __init__(self):
        self.config_tools = ConfigTools()
        self.slack_tools = SlackTools()
        self.mongo_tools = MongoTools()

        self.slack_client = self.slack_tools.get_slack_client()
        self.channel_id = self.slack_tools.get_channel_id()

        self.gardening_days = self.config_tools.get_gardening_days()
        self.start_date = self.config_tools.get_start_day()

        self.users_with_slackname = self.config_tools.load_users()
        self.users = list(self.users_with_slackname.keys())

    def get_gardening_days(self):
        return self.gardening_days

    '''
    github userid - slack username
    '''
    def get_users_with_slackname(self):
        return self.users_with_slackname

    def get_users(self):
        return self.users

    def find_attend(self, oldest, latest):
        print("find_attend")
        print(oldest)
        print(datetime.fromtimestamp(oldest))
        print(latest)
        print(datetime.fromtimestamp(latest))

        mongo_collection = self.mongo_tools.get_collection()

        for message in mongo_collection.find(
                {"ts_for_db": {"$gte": datetime.fromtimestamp(oldest), "$lt": datetime.fromtimestamp(latest)}}):
            print(message["ts"])
            print(message)

    # 특정 유저의 전체 출석부를 생성함
    # TODO 출석부를 DB에 넣고 마지막 생성된 출석부 이후의 데이터로 추가 출석부 만들도록 하자
    def find_attendance_by_user(self, user):
        mongo_collection = self.mongo_tools.get_collection()

        result = {}

        start_date = self.start_date
        for message in mongo_collection.find({"attachments.author_name": user}).sort("ts", 1):
            # make attend
            commits = []
            for attachment in message["attachments"]:
                try:
                    # commit has text field
                    # there is no text field in pull request, etc...
                    commits.append(attachment["text"])
                except Exception as err:
                    print(message["attachments"])
                    print(err)
                    continue

            # skip - if there is no commits
            if len(commits) == 0:
                continue

            # ts_datetime = datetime.fromtimestamp(float(message["ts"]))
            ts_datetime = message["ts_for_db"]
            attend = {"ts": ts_datetime, "message": commits}

            # current date and date before day1
            date = ts_datetime.date()
            date_before_day1 = date - timedelta(days=1)
            hour = ts_datetime.hour

            if date_before_day1 >= start_date and hour < 2 and date_before_day1 not in result:
                # check before day1. if exists, before day1 is already done.
                result[date_before_day1] = []
                result[date_before_day1].append(attend)
            else:
                # create date commits array
                if date not in result:
                    result[date] = []

                result[date].append(attend)

        return result

    # github 봇으로 모은 slack message 들을 slack_messages collection 에 저장
    def collect_slack_messages(self, oldest, latest):

        response = self.slack_client.conversations_history(
            channel=self.channel_id,
            latest=str(latest),
            oldest=str(oldest),
            count=1000
        )

        mongo_collection = self.mongo_tools.get_collection()

        for message in response["messages"]:
            message["ts_for_db"] = datetime.fromtimestamp(float(message["ts"]))
            # pprint.pprint(message)

            try:
                mongo_collection.insert_one(message)
            except pymongo.errors.DuplicateKeyError as err:
                print(err)
                continue

    """
    db 에 수집한 slack 메시지 삭제
    """
    def remove_all_slack_messages(self):
        mongo_collection = self.mongo_tools.get_collection()
        mongo_collection.remove()

    """
    특정일의 출석 데이터 불러오기
    @param selected_date
    """
    def get_attendance(self, selected_date):
        attend_dict = {}

        # get all users attendance info
        for user in self.users:
            attends = self.find_attendance_by_user(user)
            attend_dict[user] = attends

        result = {}
        result_attendance = []

        # make users - dates - first_ts
        for user in attend_dict:
            if user not in result:
                result[user] = {}

            result[user][selected_date] = None

            if selected_date in attend_dict[user]:
                result[user][selected_date] = attend_dict[user][selected_date][0]["ts"]

            result_attendance.append({"user": user, "first_ts": result[user][selected_date]})

        return result_attendance

    def send_no_show_message(self):
        members = self.get_users_with_slackname()
        today = datetime.today().date()

        message = "[미출석자 알람]\n"
        results = self.get_attendance(today)
        for result in results:
            if result["first_ts"] is None:
                message += "@%s " % members[result["user"]]["slack"]

        self.slack_client.chat_postMessage(
            channel='#gardening-for-100days',
            text=message,
            link_names=1
        )

