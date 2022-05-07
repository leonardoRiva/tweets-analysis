
import json, random, string, requests
from time import sleep
from datetime import datetime

from credentials import *



class TweetsDownloader():
    """
    Tweets download using Full-archive search with Academic Access

    Rate limits per app:
     - 300 requests / 15 minutes (which means, on average, 1 request / 3 seconds)
     - 1 request / 1 second

    Tweets cap:
     - 10 million per month

    You need to have access to this API by having the keys, stored in the credentials.py file 
    """



    def __init__(self, language, max_results_per_request, sleep_time):
        """
        Class initialization. The url for the http request and the fields to retrieve are already initialized. 

        Args: 
            language: two-letters country code.
            max_results_per_request: between 10 and 500
            sleep_time: sleep between each request (to avoid exceeding the rate limit). 
        """
        self.language = language
        self.max_results_per_request = str(max_results_per_request)
        self.sleep_time = sleep_time

        self.search_url = "https://api.twitter.com/2/tweets/search/all"
        self.tweet_fields = ['created_at', 'geo', 'public_metrics', 'source', 'entities']
        self.user_fields = ['description', 'location', 'public_metrics', 'verified']
        self.place_fields = ['id', 'full_name', 'place_type', 'country', 'contained_within', 'geo']



    def download(self, keywords, dates_range, filename, next_token=None, max_requests=-1, verbose=True):
        """
        Download and save tweets by making an http get request to Twitter API 2.0.

        Args: 
            keywords: list of keywords which have to be present in the tweets (retrieved if one keyword is inside the text).
            dates_range: tuple with start and end date; format: ("yyyy-mm-dd", "yyyy-mm-dd")
            filename: destination base-filename. 
            next_token: token for consecutive requests; can be found inside the previous tweet payload. 
            max_requests: how many requests will be performed at max; if -1, the requests will continue till every tweet in the dates range is downloaded. 
            verbose: if True, prints a "." everytime a request is performed correctly
        
        Raises:
            Exception: when http request isn't performed correctly. 
        """
        i = 0
        old_token = ''
        if next_token is None:
            next_token = '0000000000' + ''.join(random.choices(string.ascii_letters + string.digits, k=35))

        while next_token != old_token and i != max_requests:
            
            req = self._http_request(keywords, dates_range, next_token)
            
            if req.status_code != 200:
                raise Exception('Http request failed. Response code: ' + str(req.status_code))

            if verbose:
                print('.', end='')
            name = filename + '_' + next_token + '.json'
            self._save_file(req.text, name)
            sleep(self.sleep_time)
            
            old_token = next_token

            tweets_meta = self._read_file(name)['meta']
            if 'next_token' in tweets_meta:
                next_token = tweets_meta['next_token']

            i += 1



    def _http_request(self, keywords, dates_range, next_token):
        """
        Perform an http request to the Twitter API 2.0. 

        Args:
            keywords: list of keywords which have to be present in the tweets (retrieved if one keyword is inside the text).
            dates_range: tuple with start and end date; format: ("yyyy-mm-dd", "yyyy-mm-dd")
            next_token: token for consecutive requests; can be found inside the previous tweet payload. 

        Returns:
            The http request object. 
        """
        query = '(' + '%20OR%20'.join(['"' + x+'"' if ' ' in x else x for x in keywords]) + ')%20lang%3A' + self.language
        
        url = self.search_url + "?query=" + query
        if next_token[:10] != '0000000000':
            url += "&next_token=" + next_token
        url += "&start_time=" + dates_range[0] + 'T00:00:00.00Z'
        url += "&end_time=" + dates_range[1] + 'T00:00:00.00Z'
        url += "&tweet.fields=" + ','.join(self.tweet_fields)
        url += "&expansions=author_id,geo.place_id"
        url += "&user.fields=" + ','.join(self.user_fields)
        url += "&place.fields=" + ','.join(self.place_fields)
        url += "&max_results=" + self.max_results_per_request
        
        headers = {"Authorization": "Bearer "+BEARER_TOKEN}
        
        return requests.get(url, headers=headers)



    def merge_tweets(self, filenames, new_filename):
        """
        Merge tweets content, information and places from different requests into a single one, while fixing their format. 

        Args:
            filenames: list of the tweets filenames. 
            new_filename: base filename for the destination of the final dictionary. 
        """
        self._merge_tweets_content(filenames, new_filename + '_contents.json')
        self._merge_users_info(filenames, new_filename + '_users.json')
        self._merge_places(filenames, new_filename + '_places.json')



    def _merge_tweets_content(self, filenames, new_filename):
        """
        Merge tweets from different requests into a single one, while fixing their format. 

        Args:
            filenames: list of the tweets filenames. 
            new_filename: destination of the final dictionary. 
        """
        tweets = []
        for f in filenames:
            tmp = self._read_file(f)['data']
            for tweet in tmp:
                self._fix_tweet(tweet)
            tweets += tmp
        self._save_file(tweets, new_filename, 'json')



    def _fix_tweet(self, tweet):
        """
        Operates on a tweet by flattening some fields, fixing the datetime format and the retweet field. 

        Args:
            tweet: dictionary containing a tweet. 
        """
        # fix datetime
        tweet['datetime'] = str(datetime.strptime(tweet['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ"))
        del tweet['created_at']
        
        # fix hashtags
        if 'entities' in tweet:
            if 'hashtags' in tweet['entities']:
                tweet['hashtags'] = [h['tag'] for h in tweet['entities']['hashtags']]
            del tweet['entities']
        
        # fix retweets
        if tweet['text'].startswith('RT '):
            tweet['text'] = tweet['text'][3:]
            tweet['is_retweet'] = True
        else:
            tweet['is_retweet'] = False

        # flatten metrics
        for k,v in tweet['public_metrics'].items():
            tweet[k] = v
        del tweet['public_metrics']
            

            
    def _merge_users_info(self, filenames, new_filename):
        """
        Merge users information from different requests into a single one, while fixing their format. 

        Args:
            filenames: list of the tweets filenames. 
            new_filename: destination of the final dictionary. 
        """
        users = []
        for f in filenames:
            users += self._read_file(f)['includes']['users']
            
        # set
        users = list({u['id']:u for u in users}.values())
                    
        # flatten 
        for user in users:
            for k,v in user['public_metrics'].items():
                    user[k] = v
            del user['public_metrics']
                    
        # save new file
        self._save_file(users, new_filename, 'json')



    def _merge_places(self, filenames, new_filename):
        """
        Merge tweets places from different requests into a single one, while fixing their format. 

        Args:
            filenames: list of the tweets filenames. 
            new_filename: destination of the final dictionary. 
        """
        # concatenate places
        places = []
        for f in filenames:
            tmp = self._read_file(f)['includes']
            if 'places' in tmp:
                places += tmp['places']

        # flatten coordinates
        for p in places:
            p['bounding_box'] = p['geo']['bbox']
            del p['geo']
            
        # save new file
        self._save_file(places, new_filename, 'json')



    def _read_file(self, filename):
        """
        Read a json file containing tweets. 

        Args:
            filename: name of the json file. 

        Returns:
            A dictionary containing the tweets. 
        """
        with open(filename, 'r', encoding='utf-8') as f:
            tweets = json.load(f)
        return tweets



    def _save_file(self, text, filename, _type='txt'):
        """
        Write a dictionary containing tweets to a json file. 

        Args:
            filename: name of the json file. 
            _type: format of the file, either "txt" or "json"
        """
        if _type == 'txt':
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(text)
        elif _type == 'json':
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(text, f)

