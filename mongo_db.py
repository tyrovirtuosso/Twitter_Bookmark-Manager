from pymongo import MongoClient
from pymongo.errors import AutoReconnect
import pandas as pd
import pymongo
from dotenv import load_dotenv
load_dotenv()
import logging
logging.basicConfig(filename='mongo_db.log', level=logging.DEBUG)

from config import MONGO_CLOUD, MONGODB_CLUSTER_LOCAL, MONGODB_CLUSTER_CLOUD, db_name

class MongoDB():
    def __init__(self) -> None:
        if MONGO_CLOUD:
            cluster = MONGODB_CLUSTER_CLOUD
            self.client = MongoClient(cluster)
        else: 
            cluster = MONGODB_CLUSTER_LOCAL
            self.client = MongoClient(cluster)
        
        self.db = self.get_db(db_name=db_name)
                 
     
    def check_collection(self, collection_name):
        if collection_name in self.db.list_collection_names():
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
    
    def get_collection(self, collection_name):        
        if not self.check_collection(collection_name):            
            collection = self.db.create_collection(collection_name)  
            if 'bookmarks' in collection_name: 
                print(f"Creating {collection_name} collection")
                index_name = 'unique_id_url'
                unique_index = [('id', pymongo.ASCENDING), ('url', pymongo.ASCENDING)]
                collection.create_index(unique_index, unique=True, name=index_name)          
            return collection
        collection = self.db[collection_name]        
        return collection
    
    def fetch_from_collection(self, collection_name):
        collection = self.get_collection(collection_name)
        data = list(collection.find())
        df = pd.DataFrame(data)
        if db_name == 'Twitter':
            df['created_at'] = pd.to_datetime(df['created_at'])
            # df = df.sort_values(by='created_at', ascending=False)
        return df

    def save_to_collection(self, data, collection_name):
        collection = self.get_collection(collection_name)
        data = data.to_dict('records') 
        
        if 'bookmarks' in collection_name:
            try:
                collection.insert_many(data, ordered=False) # attempts to insert the Python dictionary objects in data into collection. If the insertion operation fails, the operation will carry on inserting any other documents that were valid.
                print("Bookmarks added to MongoDB successfully.")
                
            except pymongo.errors.BulkWriteError as e:
                write_errors = e.details.get('writeErrors', [])
                num_of_duplicates = len(write_errors)
                print(f"\n{num_of_duplicates} Duplicates Found. Duplicate Bookmarks Not Added")
        
        # for url in collection.distinct('url'):
        #     result = collection.delete_many({'url': url})  # remove all but the first document with the same url
        #     print(f"Deleted {result.deleted_count - 1} duplicates for url '{url}'")
        
                        
    def collection_item_count(self, collection_name):
        collection = self.get_collection(collection_name)
        total_count = collection.count_documents({})
        return total_count

    def delete_bookmarks_from_collection(self, collection_name, tweet_ids):
        collection = self.get_collection(collection_name)
        result = collection.delete_many({'id': {'$in': tweet_ids}})
        print(f"Deleted {result.deleted_count} bookmarks from DB")
        
        
if __name__ == "__main__":
    mongo = MongoDB()
    mongo.check_db('Twitter')

