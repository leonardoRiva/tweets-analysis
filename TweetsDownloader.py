
import json
import random, string
import requests
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

    You need to have a credentials.py file with the keys...
    """


    def __init__(self, language, max_results_per_request, sleep_time):
        self.language = language
        self.max_results_per_request = str(max_results_per_request)
        self.sleep_time = sleep_time
        self.tweet_fields = ['created_at', 'geo', 'public_metrics', 'source', 'entities']
        self.user_fields = ['description', 'location', 'public_metrics', 'verified']
        self.place_fields = ['id', 'full_name', 'place_type', 'country', 'contained_within', 'geo']


    def download(self, url, keywords, dates_range, filename, next_token=None, max_requests=None):
        """Download tweets making a http get request to Twitter API 2.0.

        Args:
            url: aaa. 
            keywords: aaa.
            dates_range: aaa. 
            filename: aaa. 
            next_token: aaa. 
            max_request: aaa. 
        """
        i = 0
        old_token = ''
        if next_token == None:
            next_token = '0000000000' + ''.join(random.choices(string.ascii_letters + string.digits, k=35))

        while next_token != old_token:
            
            req = self.tweets_request(url, keywords, next_token, dates_range)
            
            if req.ok:
                print('.', end='')
                name = filename + '_' + next_token + '.json'
                self.save_file(req.text, name)
                tweets = self.read_file(name)
                sleep(self.sleep_time)
                
            else:
                print('Error!', req)
                break
            
            old_token = next_token
            if 'next_token' in tweets['meta']:
                next_token = tweets['meta']['next_token']

            i += 1
            if max_requests and i == max_requests:
                break



    def tweets_request(self, url, keywords, next_token, dates_range):
        """request

        Args:
            ...

        Returns:
            The http request

        """
        query = '(' + '%20OR%20'.join(['"' + x+'"' if ' ' in x else x for x in keywords]) + ')%20lang%3A' + self.language
        
        url += "?query=" + query
        if next_token is not None and next_token[:10] != '0000000000':
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



    def read_file(self, filename):
        with open(filename, 'r', encoding='utf-8') as f:
            tweets = json.load(f)
        return tweets



    def save_file(self, text, filename, _type='txt'):
        if _type == 'txt':
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(text)
        elif _type == 'json':
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(text, f)



    def _fix_tweet(self, tweet):
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



    def merge_fix_tweets(self, filenames, new_filename):
        tweets = []
        for f in filenames:
            tmp = self.read_file(f)['data']
            for tw in tmp:
                self._fix_tweet(tw)
            tweets += tmp
        self.save_file(tweets, new_filename, 'json')
            

            
    def merge_users_info(self, filenames, new_filename):
        users = []
        for f in filenames:
            users += self.read_file(f)['includes']['users']
            
        # set
        users = list({u['id']:u for u in users}.values())
                    
        # flatten 
        for user in users:
            for k,v in user['public_metrics'].items():
                    user[k] = v
            del user['public_metrics']
                    
        # save new file
        self.save_file(users, new_filename, 'json')



    def merge_places(self, filenames, new_filename):
        places = []
        for f in filenames:
            tmp = self.read_file(f)['includes']
            if 'places' in tmp:
                places += tmp['places']

        for p in places:
            p['bounding_box'] = p['geo']['bbox']
            del p['geo']
            
        # save new file
        self.save_file(places, new_filename, 'json')

