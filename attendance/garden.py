from datetime import date, timedelta, datetime
import pprint
from attendance.slack_tools import SlackTools
from attendance.db_tools import DBTools
from attendance.config_tools import ConfigTools


class Garden:
    def __init__(self):
        self.config_tools = ConfigTools()
        self.slack_tools = SlackTools()
        self.db_tools = DBTools()

        self.slack_client = self.slack_tools.get_slack_client()
        self.channel_id = self.slack_tools.get_channel_id()

        self.gardening_days = self.config_tools.get_gardening_days()
        self.start_date = self.config_tools.get_start_date()
        self.start_date_str = self.config_tools.get_start_date_str()

        self.users_with_slackname = self.config_tools.get_users()
        self.users = list(self.users_with_slackname.keys())

    def get_gardening_days(self):
        return self.gardening_days

    def get_start_date(self):
        return self.start_date

    def get_start_date_str(self):
        return self.start_date_str

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

        filters = {
            'ts_for_db_gte': datetime.fromtimestamp(oldest),
            'ts_for_db_lt': datetime.fromtimestamp(latest)
        }
        
        messages = self.db_tools.find_slack_messages(filters=filters)
        
        for message in messages:
            print(message["ts"])
            print(dict(message))

    # 특정 유저의 전체 출석부를 생성함
    # TODO 출석부를 DB에 넣고 마지막 생성된 출석부 이후의 데이터로 추가 출석부 만들도록 하자
    def find_attendance_by_user(self, user):
        result = {}

        start_date = self.start_date
        
        filters = {'author_name': user}
        messages = self.db_tools.find_slack_messages(filters=filters, sort_by="ts")
        
        for message in messages:
            # make attend
            commits = []
            # PostgreSQL JSONB에서 attachments 가져오기
            attachments = message["attachments"] if message["attachments"] else []
            for attachment in attachments:
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

        import json
        
        for message in response["messages"]:
            message["ts_for_db"] = datetime.fromtimestamp(float(message["ts"]))
            # pprint.pprint(message)

            try:
                # PostgreSQL에 메시지 삽입
                insert_query = """
                    INSERT INTO slack_messages (ts, ts_for_db, bot_id, type, text, "user", team, bot_profile, attachments)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ts) DO NOTHING
                """
                
                params = (
                    message.get('ts'),
                    message.get('ts_for_db'),
                    message.get('bot_id'),
                    message.get('type'),
                    message.get('text'),
                    message.get('user'),
                    message.get('team'),
                    json.dumps(message.get('bot_profile')) if message.get('bot_profile') else None,
                    json.dumps(message.get('attachments')) if message.get('attachments') else None
                )
                
                self.db_tools.execute_query(insert_query, params, fetch_all=False)
            except Exception as err:
                print(err)
                continue

    """
    db 에 수집한 slack 메시지 삭제
    """
    def remove_all_slack_messages(self):
        delete_query = "DELETE FROM slack_messages"
        self.db_tools.execute_query(delete_query, fetch_all=False)

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

