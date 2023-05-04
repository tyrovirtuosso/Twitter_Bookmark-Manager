import base64
import hashlib
import os
import re
import json
import requests
from requests_oauthlib import OAuth2Session
from flask import Flask, redirect, session, request, url_for
import pickle
import time

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(50)

client_id = os.environ.get("CLIENT_ID")
client_secret = os.environ.get("CLIENT_SECRET")
auth_url = "https://twitter.com/i/oauth2/authorize"
token_url = "https://api.twitter.com/2/oauth2/token"
redirect_uri = os.environ.get("REDIRECT_URI")

# Set the scopes
scopes = ["tweet.read", "users.read", "tweet.write", "offline.access", "bookmark.read", "bookmark.write"]

# Create a code verifier
code_verifier = base64.urlsafe_b64encode(os.urandom(30)).decode("utf-8")
code_verifier = re.sub("[^a-zA-Z0-9]+", "", code_verifier)

print()
# Create a code challenge
code_challenge = hashlib.sha256(code_verifier.encode("utf-8")).digest()
code_challenge = base64.urlsafe_b64encode(code_challenge).decode("utf-8")
code_challenge = code_challenge.replace("=", "")

def make_token():
    return OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scopes)

    
@app.route("/welcome")
def welcome():
    response = {'message': "Welcome"}
    return response

@app.route("/")
def demo():
    global twitter
    twitter = make_token()
    
    try:
        authorization_url, state = twitter.authorization_url(
            "https://twitter.com/i/oauth2/authorize", code_challenge=code_challenge, code_challenge_method="S256"
        )
        session["oauth_state"] = state
        return redirect(authorization_url)

    except Exception as e:
        print(f"Error occurred while attempting OAuth: {str(e)}")
        return {"message": "Internal Server Error"}


@app.route("/oauth/callback", methods=["GET"])
def callback():
    code = request.args.get("code")
    state = request.args.get("state")
    access_denied = request.args.get('error')
    if access_denied:
        return {'message': "Error, the OAuth request was denied by this user"}
    
    try:
        token = twitter.fetch_token(
            token_url=token_url,
            client_secret=client_secret,
            code_verifier=code_verifier,
            code=code,
        )
        print(token)
        # Serialize the dictionary to a binary file
        with open("token.pickle", "wb") as f:
            pickle.dump(token, f)

        st_token = '"{}"'.format(token)
        j_token = json.loads(st_token)
        return redirect(url_for("welcome"))
    
    except Exception as e:
        print(f"Error occurred while fetching token: {str(e)}")
        return {"message": "Internal Server Error", "status": 500}

if __name__ == "__main__":
    app.run(port=5000, debug=True)
