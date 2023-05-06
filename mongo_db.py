from pymongo import MongoClient
from pymongo.errors import AutoReconnect
import os
import requests
from dotenv import load_dotenv
load_dotenv()
import logging
logging.basicConfig(filename='mongo_db.log', level=logging.DEBUG)


from config import MONGO_CLOUD, MONGODB_CLUSTER_LOCAL, MONGODB_CLUSTER_CLOUD

class MongoDB():
    def __init__(self) -> None:
        if MONGO_CLOUD:
            cluster = MONGODB_CLUSTER_CLOUD
            self.client = MongoClient(cluster)
        else: 
            cluster = MONGODB_CLUSTER_LOCAL
            self.client = MongoClient(cluster)
     
    def check_collection(self, db_name, collection_name):
        if collection_name in db_name.list_collection_names():
            return True
        
    def check_db(self, db_name:str):
        if db_name in self.client.list_database_names():
            return True
    
    def ping_server(self):
        for i in range(3):
            # Test DB Connection
            try:
                self.client.admin.command('ping')
                # print("Pinged your deployment. You successfully connected to MongoDB!")
                return True
            except Exception as e:                
                logging.info(f'An AutoReconnect exception occurred. {e}')
                print(f'\nAn exception occurred. Trying Again...')
                if i == 2:
                    print("Please check if IP is whitelisted on Database Server")
                    return False
    
    def get_db(self, db_name): 
        if self.ping_server():  
            if not self.check_db(db_name):
                db = self.client[db_name]
                return db
            db = self.client[db_name]
            return db
        else: 
            print("Aborting Program without saving to Database")
            import sys
            sys.exit(1)
    
    def get_collection(self, db, collection_name):        
        if not self.check_collection(db, collection_name):            
            collection = db.create_collection(collection_name)
            collection.create_index("url", unique=True)
            return collection
        collection = db[collection_name]
        collection.create_index("url", unique=True)
        return collection
        
if __name__ == "__main__":
    mongo = MongoDB()
    mongo.check_db('Twitter')

