import base64
import hashlib
import os
import re
import json
import requests
from requests_oauthlib import OAuth2Session
from fastapi import FastAPI, Request, status
from fastapi.responses import RedirectResponse, JSONResponse
import pickle
import time
from config import twitter_scopes
from dotenv import load_dotenv
from uvicorn.main import run

load_dotenv()

app = FastAPI()
# Variables
client_id = os.environ.get("CLIENT_ID")
client_secret = os.environ.get("CLIENT_SECRET")
auth_url = "https://twitter.com/i/oauth2/authorize"
token_url = "https://api.twitter.com/2/oauth2/token"
redirect_uri = os.environ.get("REDIRECT_URI")

# Set the scopes
scopes = twitter_scopes

# Create a code verifier
code_verifier = base64.urlsafe_b64encode(os.urandom(30)).decode("utf-8")
code_verifier = re.sub("[^a-zA-Z0-9]+", "", code_verifier)

def make_token():
    return OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scopes)

@app.get("/welcome")
def welcome():
    response = {"message": "Welcome"}
    return response

@app.get("/")
def root_fn():
    global twitter
    twitter = make_token()

    # Create a code challenge
    code_challenge = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode("utf-8")
    code_challenge = code_challenge.replace("=", "")

    try:
        authorization_url, state = twitter.authorization_url(
            auth_url, code_challenge=code_challenge, code_challenge_method="S256"
        )
        return RedirectResponse(authorization_url, status_code=status.HTTP_302_FOUND)

    except Exception as e:
        print(f"Error occurred while attempting OAuth: {str(e)}")
        return JSONResponse(content={"message": "Internal Server Error"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@app.get("/oauth/callback")
def callback(code: str, state: str, error: str = None):
    if error:
        return JSONResponse(content={"message": "Error, the OAuth request was denied by this user"}, status_code=status.HTTP_403_FORBIDDEN)
    
    try:
        token = twitter.fetch_token(
            token_url=token_url,
            client_secret=client_secret,
            code_verifier=code_verifier,
            code=code,
        )

        # Serialize the dictionary to a binary file
        with open("token.pickle", "wb") as f:
            pickle.dump(token, f)
        response = RedirectResponse("/welcome", status_code=status.HTTP_302_FOUND)
        return response
    
    except Exception as e:
        print(f"Error occurred while fetching token: {str(e)}")
        return JSONResponse(content={"message": "Internal Server Error"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

if __name__ == "__main__":
    run(app, host='127.0.0.1', port=5000)