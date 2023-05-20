import requests
import os
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv
load_dotenv()

from config import twitter_scopes
from mongo_db import mongo

redirect_uri = os.environ.get("REDIRECT_URI")
client_id = os.environ.get("CLIENT_ID")


class Token_Manager():
    def __init__(self):
        self.client_id = os.environ.get("CLIENT_ID")
        self.client_secret = os.environ.get("CLIENT_SECselfRET")
        self.token_url = "https://api.twitter.com/2/oauth2/token"
    
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
        print(user_id.json())
        print()
        self.user_id = user_id.json()['data']['id']
        return self.user_id

    def save_token(self, refreshed_token):
        collection_name = 'user_tokens'
        user_id = self.get_userid(refreshed_token)
        new_token_entry = {"user_id": user_id, "token": refreshed_token}        
        mongo.save_to_collection(new_token_entry, collection_name, user_id)

    def refresh_token(self, token):
        twitter = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=twitter_scopes)
        refreshed_token = twitter.refresh_token(
            client_id=self.client_id,
            client_secret=self.client_secret,
            token_url=self.token_url,
            refresh_token=token["refresh_token"],
        )
        self.save_token(refreshed_token)
        return refreshed_token

tm = Token_Manager()

if __name__ == "__main__":
    print("Executing TokenManager as main file")