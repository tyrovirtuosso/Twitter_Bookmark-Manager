import requests
import pandas as pd
from termcolor import colored
import logging
logging.basicConfig(filename='bookmarks.log', level=logging.DEBUG)

class Bookmarks():
    def __init__(self) -> None:
        pass
    
    def get_all_bookmarks(self, user_fields=None, media_fields=None, tweet_fields=None, expansions=None, limit=None, pagination_token=None):
        """
        Fetches and processes a user's bookmarks from Twitter.

        Args:
        - user_fields: Optional; str or list of str representing fields to include in the returned users object(s).
        - media_fields: Optional; str or list of str representing fields to include in the returned media object(s).
        - tweet_fields: Optional; str or list of str representing fields to include in the returned Tweets object(s).
        - expansions: Optional; str or list of str representing expansions to include in the response.
        - limit: Optional; int representing maximum items to return per request. The default limit is set to
          100 by Twitter API, which is also the maximum, but it can be set to a custom value from within this method.
        - pagination_token: Optional; str representing token used to retrieve the next page of results.

        Returns:
        pandas.DataFrame of tweets containing the following columns:
        - id: tweet ID
        - text: tweet text
        - created_at: time at which the tweet was created
        - impression_count: number of impressions (views) of tweet
        - like_count: number of likes received by the tweet
        - reply_count: number of replies received by the tweet
        - retweet_count: number of times the tweet has been retweeted
        - name: name of tweet author
        - username: username of tweet author
        - url: URL redirecting to tweet on Twitter.com

        It does this by calling self.get_bookmarks() and processing the returned JSON data. Pagination is handled
        automatically within this method.

        Raises:
        - Exception if there was an error retrieving bookmarks from Twitter API.
        """
        
        bookmarks = []
        count = limit                
        print("")
        for i in range(1, 1000):  # Set upper bound to avoid infinite loop    
            response = self.get_bookmarks(user_fields=user_fields, media_fields=media_fields, tweet_fields=tweet_fields, expansions=expansions, limit=limit, pagination_token=pagination_token)
            response_data = response.json()
            print()
            print(f"Fetched total of {colored(count, 'green')} bookmarks")
            logging.info(f"Fetched total of {colored(count, 'green')} bookmarks")
            count += limit     
                   
            if response.status_code != 200:
                logging.error(f"Error retrieving bookmarks: {response_data['error']['message']}")
                raise Exception(f"Error retrieving bookmarks: {response_data['error']['message']}")
            
            if len(response_data["data"]) == 0:                
                logging.info(f"Finished Fetching bookmarks!")
                break  # If there are no more bookmarks, break the loop
            
            bookmark = self.process_bookmark_dict(response.json())
            bookmarks.append(bookmark)                                    
            
            if "next_token" in response_data.get("meta", {}):  # If there are more pages, get the next page
                pagination_token = response_data.get("meta", {}).get("next_token")
            else:
                break  # If there are no more pages, break the loop        
        return bookmarks
    
    def get_bookmarks(self, user_fields=None, media_fields=None, tweet_fields=None, expansions=None, limit=2, pagination_token=None):        
        """
        Issues a GET request to the Twitter API to retrieve a user's bookmarked tweets.

        Args:
        - user_fields: Optional; str or list of str representing fields to include in the returned users object(s).
        - media_fields: Optional; str or list of str representing fields to include in the returned media object(s).
        - tweet_fields: Optional; str or list of str representing fields to include in the returned Tweets object(s).
        - expansions: Optional; str or list of str representing expansions to include in the response.
        - limit: Optional; int representing maximum items to return per request. The default limit is set to
          25 by Twitter API, but it can be set to a custom value from within this method.
        - pagination_token: Optional; str representing token used to retrieve the next page of results.

        Returns:
        requests.Response object representing the API response.

        Raises:
        - None.
        """
        url = f"https://api.twitter.com/2/users/{self.user_id}/bookmarks"
        params = {"max_results": limit}
        params.update({'user.fields': ','.join(user_fields)} if user_fields else {})
        params.update({'tweet.fields': ','.join(tweet_fields)} if tweet_fields else {})
        params.update({'media.fields': ','.join(media_fields)} if media_fields else {})
        params.update({'expansions': ','.join(expansions)} if expansions else {})
        params.update({'pagination_token': pagination_token} if pagination_token else {})
        headers = {
            "Authorization": f"Bearer {self.token['access_token']}",
        }
        response = send_request('GET', url, headers=headers, params=params)
        # print(headers)
        # print(f"Requesting to {response.url} and {response.headers}")
        return response
    
    def process_bookmark_dict(self, bookmark_dict):
        """
        Processes a dictionary of bookmarked tweets returned from the Twitter API.

        Args:
        - bookmark_dict: dictionary containing bookmarks data in JSON format.

        Returns:
        pandas.DataFrame of tweets containing the following columns:
        - id: tweet ID
        - text: tweet text
        - created_at: time at which the tweet was created
        - impression_count: number of impressions (views) of tweet
        - like_count: number of likes received by the tweet
        - reply_count: number of replies received by the tweet
        - retweet_count: number of times the tweet has been retweeted
        - name: name of tweet author
        - username: username of tweet author
        - url: URL redirecting to tweet on Twitter.com

        It does this by iterating over bookmark_dict and extracting relevant data, saving it to a list, then processing
        the resulting list into a pandas DataFrame.

        Raises:
        - None.
        """
        
        print()
        tweets = []
        for d in bookmark_dict['data']:
            tweet = {'id': d['id'], 'text': d['text'], 'created_at': d['created_at'], 
                    'impression_count': d['public_metrics']['impression_count'], 'like_count': d['public_metrics']['like_count'],
                    'reply_count': d['public_metrics']['reply_count'], 'retweet_count': d['public_metrics']['retweet_count']}
            author_id = d['author_id']
            for user in bookmark_dict['includes']['users']:
                if user['id'] == author_id:
                    tweet['name'] = user['name']
                    tweet['username'] = user['username']
                    tweet['url'] = f"https://twitter.com/{tweet['username']}/status/{tweet['id']}"
                    break
            tweets.append(tweet)
        df = pd.DataFrame(tweets)        
        return df

    def start_fetching_bookmarks(self, user_id, token):
        self.token = token
        self.user_id = user_id
        bookmarks = self.get_all_bookmarks(user_fields=["username"], tweet_fields=["author_id","created_at","public_metrics"], expansions=["author_id"], limit=100)        
        all_bookmarks = pd.concat(bookmarks, ignore_index=True)
        return all_bookmarks
    
    def delete_bookmarks(self, user_id, token, tweet_id):
        url = f"https://api.twitter.com/2/users/{user_id}/bookmarks/{tweet_id}"
        headers = {
            "Authorization": f"Bearer {token['access_token']}",
        }
        response = send_request('DELETE', url, headers=headers)
        # print(headers)
        # print(f"Requesting to {response.url} and {response.headers}")            
    
def send_request(method, url, headers=None, params=None, json=None):
    """
    Sends an HTTP request to a website using the specified method, url, headers, params, and/or JSON data.

    Args:
    - method: str representing HTTP method to use (GET, POST, PUT, etc.).
    - url: str representing the URL to send the request to.
    - headers: Optional; dict representing headers to be included in the request.
    - params: Optional; dict representing parameters to be included in the request.
    - json: Optional; JSON-serializable data to be included in the request body.

    Returns:
    requests.Response object representing the API response.

    Raises:
    - None.
    """

    req = requests.Request(method, url, headers=headers, params=params, json=json)
    prepped = req.prepare()
    return requests.Session().send(prepped)


bookmark_manager = Bookmarks()