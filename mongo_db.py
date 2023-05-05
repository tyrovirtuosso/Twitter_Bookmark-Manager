from pymongo import MongoClient
import os
from dotenv import load_dotenv
load_dotenv()

class MongoDB():
    def __init__(self) -> None:
        cluster = os.environ.get("MONGODB_CLUSTER")
        self.client = MongoClient(cluster)
     
    def check_collection(self, db_name, collection_name):
        if collection_name in db_name.list_collection_names():
            return True
        
    def check_db(self, db_name:str):
        if db_name in self.client.list_database_names():
            return True
        
if __name__ == "__main__":
    mongo = MongoDB()
    mongo.check_db('Twitter')

