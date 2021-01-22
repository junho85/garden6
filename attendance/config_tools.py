import configparser
import os
from datetime import date, timedelta, datetime
import yaml


class ConfigTools:
    def __init__(self):
        self.config = self.load_config()
        pass

    def load_config(self):
        config = configparser.ConfigParser()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, 'config.ini')
        config.read(path)
        return config

    def get_config(self):
        return self.config

    def get_gardening_days(self):
        return self.config['DEFAULT']['GARDENING_DAYS']

    def get_start_day(self):
        return datetime.strptime(self.config['DEFAULT']['START_DATE'],
                          "%Y-%m-%d").date()  # start_date e.g.) 2021-01-18

    '''
    load users.yaml
    '''
    def load_users(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))

        # users_with_slackname
        path = os.path.join(base_dir, 'users.yaml')
        with open(path) as file:
            users_with_slackname = yaml.full_load(file)

        return users_with_slackname
