from mongo_db import MongoDB
from config import db_name
from token_manager import Token_Manager
from fetcher import Fetcher

import pandas as pd
import csv
from pprint import pprint


def refresh_token(token):
    tm = Token_Manager(token)
    token = tm.refresh_token()
    return token
    


if __name__ == "__main__":
    user_id = '1327220079235239936'    
    fetcher = Fetcher(user_id)
        
    # bookmarks = (fetcher.fetch_bookmarks_from_twitter())
    # fetcher.save_to_collection(bookmarks)
    
    # df = fetcher.fetch_from_collection()
    # df.to_csv('output.csv', index=False)    
    # print(fetcher.collection_item_count())
    # fetcher.delete_bookmarks(['6454f10df087e9e96d457a91'])
    # print(fetcher.collection_item_count())
    # PendulumFlow = df[df['username'] == 'PendulumFlow']
    # PendulumFlow.to_csv('PendulumFlow.csv', index=False)    
    # document = fetcher.fetch_specific_document_from_bookmarks(column='url', search='https://twitter.com/PendulumFlow/status/1421266423553224706')
    
    print(f"Total Bookmarks: {fetcher.collection_item_count()}")
    df = fetcher.fetch_from_bookmark_collection()
    most_occured_usernames = fetcher.get_most_occured_usernames(df) 
    print((most_occured_usernames))
    
    filterd_df = fetcher.fetch_bookmarks_of_specific_usernames(df, ['Qi_Capital', 'AgilePatryk'])
    filterd_df.to_csv('filterd_df.csv', index=False)
    filterd_dict = filterd_df.to_dict(orient='records')
    for tweet in filterd_dict:   
        print()     
        pprint(tweet)
        
    excluded_urls = ['']
    filtered_df = filterd_df[~filterd_df['url'].isin(excluded_urls)]

    id_list = filterd_df['id'].tolist()

    fetcher.delete_bookmarks(id_list)
        
    print(f"Total Bookmarks: {fetcher.collection_item_count()}")
    
