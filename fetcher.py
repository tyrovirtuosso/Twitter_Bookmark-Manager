from token_manager import Token_Manager
from mongo_db import MongoDB
from bookmarks import Bookmarks
from config import db_name, collection_name

from pymongo.database import Database
from pymongo.collection import Collection
from typing import Optional
from halo import Halo
import time
import pandas as pd
from pprint import pprint
from bson import json_util


class Fetcher():
    def __init__(self, user_id) -> None:
        self.user_id = user_id
        self.mongo = MongoDB()        
        self.tm = Token_Manager(self.get_token_for_userid())
        self.token = self.tm.refresh_token()
        self.bookmarks = Bookmarks(self.token, user_id)

    
    def get_token_for_userid(self):
        user_tokens_collection = self.mongo.get_collection('user_tokens') 
        user_token_doc = user_tokens_collection.find_one({"user_id": self.user_id})
        if user_token_doc is not None:
            token = user_token_doc['token']
            return token
        else:
            print(f"No token found for user ID {self.user_id}")
    

    def get_collection(self, collection_name):
        self.collection = self.mongo.get_collection(collection_name=collection_name)
        return self.collection
    
    def get_all_columns(self, cursor: Collection):
        columns = []
        for document in cursor:   
            for key in document.keys():
                if key not in columns:
                    columns.append(key)

        return columns
    
    def time_task(self, text: str, task_func, *args, **kwargs):
        spinner = Halo(text=text, spinner='line')
        spinner.start()
        start_time = time.time()
        task_result = task_func(*args, **kwargs)
        total_time = time.time() - start_time
        spinner.stop()
        print()
        print(f"Finished in {round(total_time,2)} seconds")
        if task_result is None:
            return None
        elif isinstance(task_result, Collection) or isinstance(task_result, pd.core.frame.DataFrame):
            return task_result
        elif isinstance(task_result, (list, tuple)) and len(task_result) == 1:
            return task_result[0]
        else:
            return tuple(task_result)

    def fetch_bookmarks_from_twitter(self):        
        # bookmarks = self.bookmarks.start()
        bookmarks = self.time_task("Fetching Bookmarks from Twitter...", self.bookmarks.start_fetching_bookmarks)
        # print(bookmarks)
        return bookmarks
    
    def fetch_from_collection(self, collection_name='bookmarks_'):        
        collection_name = collection_name + self.user_id
        # data = self.mongo.fetch_from_collection(collection_name)
        data = self.time_task(f"Fetching data from MongoDB Collection {collection_name}...", self.mongo.fetch_from_collection, collection_name)        
        return data
        
    def save_to_collection(self, data, collection_name='bookmarks_'):
        collection_name = collection_name + self.user_id
        self.mongo.save_to_collection(data, collection_name)
        
    def delete_bookmarks(self, tweet_ids, collection_name='bookmarks_'):
        collection_name = collection_name + self.user_id
        self.mongo.delete_bookmarks_from_collection(collection_name, tweet_ids)   
        print(f"Deleting {len(tweet_ids)} Bookmarks from Twitter...")
        i = 1
        for tweet_id in tweet_ids:
            try:
                self.bookmarks.delete_bookmarks(tweet_id)   
                print(f"Deleted {i}/{len(tweet_ids)}", end="\r")  # Print in a single line. The carriage return character (\r) moves the cursor back to the beginning of the line
                i += 1     
            except Exception as e:
                print("API limit reached while deleting tweets, sleeping for 5 seconds")                
                time.sleep(5)                                      
        print(f"All Bookmarks Deleted!")     
                               
        
    def get_most_occured_usernames(self, data):
        return data['username'].value_counts().head(10)
    
    def collection_item_count(self, collection_name='bookmarks_'):
        collection_name = collection_name + self.user_id
        total_count = self.mongo.collection_item_count(collection_name)
        return total_count
        
        
    def fetch_specific_document_from_bookmarks(self, collection_name='bookmarks_', column='url', search=''):
        collection_name = collection_name + self.user_id
        collection = self.mongo.get_collection(collection_name)
        document = collection.find_one({column: search})
        # print the matching document (if found)
        if document:
            return document
        else:
            print(f"No document found with {column}: {search}")
    
    def fetch_from_bookmark_collection(self, collection_name='bookmarks_'):
        collection_name = collection_name + self.user_id
        collection = self.mongo.get_collection(collection_name)
        fields_to_include = {"id": 1, "text": 1, "created_at": 1, "name": 1, "username": 1, "url": 1}
        fields_to_exclude = {"_id": 0}
        documents = collection.find({}, {**fields_to_include, **fields_to_exclude})        
        data = list(documents)
        df = pd.DataFrame(data)        
        return df

    def fetch_bookmarks_of_specific_usernames(self, df, username_list):
        all_filtered_data = pd.DataFrame()
        for username in username_list:
            username_mask = df['username'] == username
            filtered_data = df[username_mask]
            all_filtered_data = pd.concat([all_filtered_data, filtered_data])
        return all_filtered_data
    
    def archive_collection(self, collection_name='bookmarks_'):
        collection_name = collection_name + self.user_id
        source_collection = self.mongo.get_collection(collection_name)
        destination_collection_name = 'archive_' + collection_name
        destination_collection = self.mongo.get_collection(destination_collection_name)
        destination_collection.insert_many(source_collection.find())
        print(f"{collection_name} archived as {destination_collection_name}")

        
            
        

if __name__ == "__main__":
    fetcher = Fetcher()
    
