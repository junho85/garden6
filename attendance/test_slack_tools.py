from unittest import TestCase

from slack_tools import SlackTools


class TestSlackTools(TestCase):
    slack_tools = SlackTools()

    def test_get_users(self):
        print(self.slack_tools.get_users())

    def test_get_user_names(self):
        print(self.slack_tools.get_user_names())

