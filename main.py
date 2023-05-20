from fetcher import fetcher

from pprint import pprint
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)
    
if __name__ == "__main__":
    user_id = redis_client.get("user_id").decode()
        
    bookmarks = fetcher.fetch_bookmarks_from_twitter(user_id)
    fetcher.save_to_collection(bookmarks, collection_name='bookmarks_', user_id=user_id)
    
    df = fetcher.fetch_from_collection(user_id=user_id)
    df.to_csv('output.csv', index=False)    
    # fetcher.delete_bookmarks(user_id, ['1659287774791618562'])
    print(f"Total Bookmarks: {fetcher.collection_item_count(user_id, collection_name='bookmarks_')}")
    most_occured_usernames = fetcher.get_most_occured_usernames(df) 
    print((most_occured_usernames))
    
    filterd_df = fetcher.fetch_bookmarks_of_specific_usernames(df, ['Qi_Capital', 'AgilePatryk'])
    filterd_df.to_csv('filterd_df.csv', index=False)
    filterd_dict = filterd_df.to_dict(orient='records')
    for tweet in filterd_dict:   
        print()     
        pprint(tweet)
        
    # excluded_urls = ['']
    # filtered_df = filterd_df[~filterd_df['url'].isin(excluded_urls)]

    id_list = filterd_df['id'].tolist()
    # fetcher.delete_bookmarks(id_list)
        
    print(f"Total Bookmarks: {fetcher.collection_item_count(user_id, collection_name='bookmarks_')}")
    
