import base64
import hashlib
import os
import re
from requests_oauthlib import OAuth2Session
from fastapi import FastAPI, Request, status
from fastapi.responses import RedirectResponse, JSONResponse, StreamingResponse, HTMLResponse
import pickle
import uvicorn
import pymongo
import urllib.parse


from config import twitter_scopes, db_name
from dotenv import load_dotenv
from mongo_db import MongoDB
from token_manager import Token_Manager
from fetcher import Fetcher

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

def add_user_token(token):
    # Initialize DB
    mongo = MongoDB()
    db = mongo.get_db(db_name)
    
    # create user_tokens collection for adding tokens of users with user_id as index
    user_tokens_collection = mongo.get_collection(db, 'user_tokens') 
    tm = Token_Manager(token)
    user_id = tm.get_userid(token)        
    user_tokens_collection.create_index([('user_id', pymongo.ASCENDING)], unique=True)   
            
    new_token = {"user_id": user_id, "token": token}
    user_tokens_collection.replace_one({"user_id": user_id}, new_token, upsert=True)
    print("Token added successfully.")


# @app.get("/welcome")
# async def welcome(request: Request):
#     token = request.cookies.get("token")
#     token = urllib.parse.parse_qs(urllib.parse.unquote(token))
#     token = {key: val[0] for key, val in token.items()}
#     tm = Token_Manager(token)
#     user_id = tm.get_userid(token)     
    
#     fetcher = Fetcher(token, user_id)  
#     fetcher.fetch_bookmarks_from_twitter() 
    
#     async def generate():      
#         yield "data: fetching\n\n"
#         time.sleep(1)
#         yield "data: still fetching\n\n"
#         time.sleep(1)
#         yield f"data: done fetching with token: {token} for {user_id} \n\n"

#     return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/welcome", response_class=HTMLResponse)
async def welcome(request: Request):
    token = request.cookies.get("token")
    token = urllib.parse.parse_qs(urllib.parse.unquote(token))
    token = {key: val[0] for key, val in token.items()}
    tm = Token_Manager(token)
    user_id = tm.get_userid(token)
    
    return f"""
        <html>
            <head>
                <title>Welcome to My App</title>
                <script>
                    function fetchBookmarks() {{
                        fetch('/fetch-bookmarks')
                            .then(response => response.json())
                            .then(data => {{
                                const bookmarksList = document.getElementById('bookmarks-list');
                                bookmarksList.innerHTML = '';
                                data.forEach(bookmark => {{
                                    const listItem = document.createElement('li');
                                    const textNode = document.createTextNode(`${{bookmark.title}} - ${{bookmark.url}}`);
                                    listItem.appendChild(textNode);
                                    bookmarksList.appendChild(listItem);
                                }});
                            }})
                            .catch(error => console.error(error));
                    }}
                </script>
            </head>
            <body>
                <h1>Welcome!</h1>
                <p>Your Twitter User ID is: {user_id}</p>
                <button onclick="fetchBookmarks()">Fetch Bookmarks</button>
                <ul id="bookmarks-list"></ul>
            </body>
        </html>
    """








@app.get("/fetch-bookmarks")
async def fetch_bookmarks(request: Request):
    token = request.cookies.get("token")
    token = urllib.parse.parse_qs(urllib.parse.unquote(token))
    token = {key: val[0] for key, val in token.items()}
    tm = Token_Manager(token)
    user_id = tm.get_userid(token)     
    
    fetcher = Fetcher(token, user_id)  
    bookmarks = fetcher.fetch_bookmarks_from_twitter()
    bookmarks_json = bookmarks.to_dict(orient='records')
    return JSONResponse(content=bookmarks_json)



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
        
        add_user_token(token)
                
        # Serialize the dictionary to a binary pickle file
        with open("token.pickle", "wb") as f:
            pickle.dump(token, f)
            
        query_params = urllib.parse.urlencode(token)
        response = RedirectResponse("/welcome", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="token", value=query_params)
        
        # response = RedirectResponse(f"/welcome?{query_params}", status_code=status.HTTP_302_FOUND)
        return response
    
    except Exception as e:
        print(f"Error occurred while fetching token: {str(e)}")
        return JSONResponse(content={"message": "Internal Server Error"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

if __name__ == "__main__":
    uvicorn.run("oauth_twitter:app", host="127.0.0.1", port=5000, reload=True)
