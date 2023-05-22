import base64
import hashlib
import os
import re
from requests_oauthlib import OAuth2Session
from fastapi import FastAPI, Request, status
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
import redis
import pickle
import uvicorn
from dotenv import load_dotenv
load_dotenv()

from config import twitter_scopes
from token_manager import tm
from fetcher import fetcher


# Variables
client_id = os.environ.get("CLIENT_ID")
client_secret = os.environ.get("CLIENT_SECRET")
auth_url = "https://twitter.com/i/oauth2/authorize"
token_url = "https://api.twitter.com/2/oauth2/token"
redirect_uri = os.environ.get("REDIRECT_URI")

REDIS_HOST = os.environ.get("REDIS_CLIENT")
REDIS_PORT = os.environ.get("REDIS_PORT")
REDIS_PASS = os.environ.get("REDIS_PASS")

# Initialize app and redis for cache
app = FastAPI()
redis_client = redis.Redis(
  host=REDIS_HOST,
  port=REDIS_PORT,
  password=REDIS_PASS)

# Set the scopes
scopes = twitter_scopes

# Create a code verifier
code_verifier = base64.urlsafe_b64encode(os.urandom(30)).decode("utf-8")
code_verifier = re.sub("[^a-zA-Z0-9]+", "", code_verifier)


def make_token():
    return OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scopes)

def add_user_token(token, user_id):    
    collection_name = 'user_tokens'
    new_token_entry = {"user_id": user_id, "token": token}        
    fetcher.save_to_collection(new_token_entry, collection_name, user_id=user_id)  

@app.get("/welcome", response_class=HTMLResponse)
async def welcome():
    user_id = redis_client.get("user_id").decode()
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
def fetch_bookmarks(request: Request):    
    user_id = redis_client.get("user_id").decode()
    bookmarks = fetcher.fetch_bookmarks_from_twitter(user_id)
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
        user_id = tm.get_userid(token)       
        add_user_token(token, user_id)
        
        # Serialize the dictionary to a binary pickle file
        with open("token.pickle", "wb") as f:
            pickle.dump(token, f)
            
        redis_client.set("user_id", user_id)
        response = RedirectResponse("/welcome", status_code=status.HTTP_302_FOUND)
        return response
    
    except Exception as e:
        print(f"Error occurred while fetching token: {str(e)}")
        return JSONResponse(content={"message": "Internal Server Error"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

if __name__ == "__main__":
    uvicorn.run("oauth_twitter:app", host="127.0.0.1", port=6000, reload=True)
