import configparser
import os
import pymongo


class MongoTools:
    def __init__(self):
        config = configparser.ConfigParser()
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(BASE_DIR, 'config.ini')
        config.read(path)

        self.mongo_database = config['MONGO']['DATABASE']
        self.mongo_host = config['MONGO']['HOST']
        self.mongo_port = config['MONGO']['PORT']

        # mongodb collections
        self.mongo_collection_slack_message = "slack_messages"


    def connect_mongo(self):
        return pymongo.MongoClient("mongodb://%s:%s" % (self.mongo_host, self.mongo_port))

    def get_database(self):
        conn = self.connect_mongo()

        return conn.get_database(self.mongo_database)

    def get_collection(self):
        db = self.get_database()

        return db.get_collection(self.mongo_collection_slack_message)
