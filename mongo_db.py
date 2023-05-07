from pymongo import MongoClient
from pymongo.errors import AutoReconnect
import os
import pandas as pd
import requests
from dotenv import load_dotenv
load_dotenv()
import logging
logging.basicConfig(filename='mongo_db.log', level=logging.DEBUG)
import pymongo


from config import MONGO_CLOUD, MONGODB_CLUSTER_LOCAL, MONGODB_CLUSTER_CLOUD, db_name

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
        print("\nConnecting to MongoDB Server...")
        for i in range(3):
            # Test DB Connection
            try:
                self.client.admin.command('ping')
                print("\nYou successfully connected to MongoDB!")
                return True
            except Exception as e:                
                logging.info(f'An AutoReconnect exception occurred. {e}')
                print(f'\nAn exception occurred while connection to DB. Trying Again...')
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
            return collection
        collection = db[collection_name]
        return collection
    
    def fetch_from_collection(self, collection_name):
        db = self.get_db(db_name)
        collection = self.get_collection(db, collection_name)
        data = collection.find().sort("start_date", pymongo.DESCENDING)
        df = pd.DataFrame(data)
        if db_name == 'Twitter':
            df['created_at'] = pd.to_datetime(df['created_at'])
            df = df.sort_values(by='created_at', ascending=False)
        return df

    def save_to_collection(self, data, collection_name):
        db = self.get_db(db_name)
        collection = self.get_collection(db, collection_name)
        data = data.to_dict('records') 
        try:
            collection.insert_many(data, ordered=False) # attempts to insert the Python dictionary objects in data into collection. If the insertion operation fails, the operation will carry on inserting any other documents that were valid.
            print("Bookmarks added to MongoDB successfully.")
            
        except pymongo.errors.BulkWriteError as e:
            write_errors = e.details.get('writeErrors', [])
            num_of_duplicates = len(write_errors)
            print(f"\n{num_of_duplicates} Duplicates Found. Duplicate Bookmarks Not Added")
        
if __name__ == "__main__":
    mongo = MongoDB()
    mongo.check_db('Twitter')

