from fetcher import Fetcher
import pandas as pd

db_name = 'Twitter'

if __name__ == "__main__":
    fetcher = Fetcher()
    bookmarks = fetcher.fetch_bookmarks_from_twitter()
    # bookmarks.to_csv('bookmarks.csv', index=False)
    # fetcher.save_to_collection(bookmarks)
    # data = fetcher.fetch_from_collection()
    # data.to_csv('output.csv', index=False)    
    
    fetcher.delete_bookmarks(['1655143714128531456'])

