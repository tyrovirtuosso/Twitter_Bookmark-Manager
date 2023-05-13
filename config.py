import os
from dotenv import load_dotenv
load_dotenv()

mongo_atlas_pass = os.environ.get("MONGODB_ATLAS_PASS")
mongo_username = os.environ.get("MONGO_USERNAME")
twitter_scopes = ["tweet.read", "users.read", "tweet.write", "offline.access", "bookmark.read", "bookmark.write"]
db_name = 'Twitter'
collection_name = 'bookmarks_'
MONGO_CLOUD = True
MONGODB_CLUSTER_LOCAL= os.environ.get("MONGODB_CLUSTER_LOCAL")
MONGODB_CLUSTER_CLOUD= f"mongodb+srv://{mongo_username}:{mongo_atlas_pass}@cluster0.qee0lg0.mongodb.net/?retryWrites=true&w=majority"
