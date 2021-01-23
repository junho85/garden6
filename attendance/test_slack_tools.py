from unittest import TestCase

from attendance.slack_tools import SlackTools
from attendance.config_tools import ConfigTools


class TestSlackTools(TestCase):
    slack_tools = SlackTools()
    config_tools = ConfigTools()

    def test_get_users(self):
        print(self.slack_tools.get_users())

    def test_get_user_names(self):
        print(self.slack_tools.get_user_names())

    def test_get_user_slacknames(self):
        print(self.config_tools.get_user_slacknames())

    '''
    slack에 있는 유저들 - users.yaml에 등록된 slack이름을 뺌. 거기다가 봇들 제외
    다 등록 되었으면 결과에 아무 유저가 나오면 안됨
    '''
    def test_user_diff(self):
        print(set(self.slack_tools.get_user_names())
              - set(self.config_tools.get_user_slacknames())
              - {"slackbot",
                 "garden6",
                 "github"})

    '''
    users.yaml에 등록된 slack이름 - slack에 있는 유저들
    '''
    def test_user_diff2(self):
        print(set(self.config_tools.get_user_slacknames())
              - set(self.slack_tools.get_user_names())
              )
