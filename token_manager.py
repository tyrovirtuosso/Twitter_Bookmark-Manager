import requests
import os
import pickle
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv
load_dotenv()

from config import twitter_scopes, db_name
from mongo_db import MongoDB

redirect_uri = os.environ.get("REDIRECT_URI")
client_id = os.environ.get("CLIENT_ID")



class Token_Manager():
    def __init__(self, token):
        self.client_id = os.environ.get("CLIENT_ID")
        self.client_secret = os.environ.get("CLIENT_SECRET")
        self.token_url = "https://api.twitter.com/2/oauth2/token"
        self.token = token
    
    def get_userid(self, token):
        url = "https://api.twitter.com/2/users/me"
        user_id = requests.request(
            "GET",
            url,
            headers={
                "Authorization": "Bearer {}".format(token["access_token"]),
                "Content-Type": "application/json",
            }
        )
        self.user_id = user_id.json()['data']['id']
        return self.user_id

    # def get_token(self, user_id):
    #     # # Load the dictionary from the pickle file
    #     # with open("token.pickle", "rb") as f:
    #     #     self.token = pickle.load(f)
        
    #     # Get token from the user_tokens collection in Twitter MongoDB
    #     # Initialize DB
    #     mongo = MongoDB()
        
    #     # Get user_tokens collection
    #     user_tokens_collection = mongo.get_collection('user_tokens') 
        
    #     # query the user_tokens collection for the specific user_id
    #     user_token_doc = user_tokens_collection.find_one({"user_id": user_id})
    #     # get the token from the document
    #     if user_token_doc is not None:
    #         token = user_token_doc['token']
    #         print(f"Token for user ID {user_id} is: {token}")
    #     else:
    #         print(f"No token found for user ID {user_id}")
            
            
    #     return self.token

    def save_token(self, refreshed_token):
        # with open("token.pickle", "wb") as f:
        #     pickle.dump(refreshed_token, f)
        
        mongo = MongoDB()
        user_tokens_collection = mongo.get_collection('user_tokens') 
        user_id = self.get_userid(refreshed_token)  
        new_token = {"user_id": user_id, "token": refreshed_token}
        user_tokens_collection.replace_one({"user_id": user_id}, new_token, upsert=True)
        

    def refresh_token(self):
        twitter = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=twitter_scopes)
        refreshed_token = twitter.refresh_token(
            client_id=self.client_id,
            client_secret=self.client_secret,
            token_url=self.token_url,
            refresh_token=self.token["refresh_token"],
        )
        self.token = refreshed_token
        self.save_token(refreshed_token)
        return self.token

if __name__ == "__main__":
    tm = Token_Manager()
    token = tm.get_token()
    token = tm.refresh_token()
    user_id = tm.get_userid(token)
