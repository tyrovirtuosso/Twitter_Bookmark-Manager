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


class Fetcher():
    def __init__(self, token, user_id) -> None:
        self.tm = Token_Manager()
        self.mongo = MongoDB()
        self.bookmarks = Bookmarks(token, user_id)

    
    @property
    def twitter_oath_token(self):
        return self.tm.refresh_token()
    
    @property
    def twitter_user_id(self):
        return self.tm.get_userid(self.twitter_oath_token)
    
    def get_db_obj(self, db_name):
        self.db = self.mongo.get_db(db_name=db_name)
        return self.db

    def get_collection(self, db_name, collection_name):
        self.collection = self.mongo.get_collection(self.get_db_obj(db_name=db_name), collection_name=collection_name)
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
        collection_name = collection_name + self.twitter_user_id
        # data = self.mongo.fetch_from_collection(collection_name)
        data = self.time_task(f"Fetching data from MongoDB Collection {collection_name}...", self.mongo.fetch_from_collection, collection_name)        
        return data
        
    def save_to_collection(self, data, collection_name='bookmarks_'):
        collection_name = collection_name + self.twitter_user_id
        self.mongo.save_to_collection(data, collection_name)
        
    def delete_bookmarks(self, user_ids):
        self.bookmarks.delete_bookmarks(user_ids)
        
    
    def get_most_occured_usernames(self, data):
        return data['username'].value_counts().head(10)
        
        
        


if __name__ == "__main__":
    fetcher = Fetcher()
    # bookmarks = fetcher.fetch_bookmarks()
    
