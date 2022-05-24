import json, random, string, requests, re
import pandas as pd
import numpy as np
from time import sleep
from datetime import datetime
from rapidfuzz import process, fuzz

from credentials import *
from TweetsUtils import *



class TweetsDownloader():
    """
    Tweets download using Full-archive search with Academic Access. 

    Rate limits per app:
     - 300 requests / 15 minutes (which means, on average, 1 request / 3 seconds)
     - 1 request / 1 second

    Tweets cap:
     - 10 million per month

    You need to have access to this API by having the keys, stored in the credentials.py file. 
    """


    def __init__(self, language, max_results_per_request, sleep_time):
        """
        Class initialization. The url for the http request and the fields to retrieve are already initialized. 

        Args: 
            language: two-letters country code.
            max_results_per_request: between 10 and 500. 
            sleep_time: sleep between each request (to avoid exceeding the rate limit). 
        """
        self.language = language
        self.max_results_per_request = str(max_results_per_request)
        self.sleep_time = sleep_time

        self.search_url = "https://api.twitter.com/2/tweets/search/all"
        self.expansions = ['referenced_tweets.id', 'author_id', 'geo.place_id']
        self.tweet_fields = ['created_at', 'geo', 'public_metrics', 'source', 'entities']
        self.user_fields = ['description', 'location', 'public_metrics', 'verified']
        self.place_fields = ['id', 'full_name', 'place_type', 'country', 'contained_within', 'geo']




    #--------------------------------
    # download functions
    #--------------------------------


    def download(self, keywords, dates_range, filename, next_token=None, max_requests=-1, original_tweets=False, verbose=True):
        """
        Downloads and saves tweets, based on keywords, between two dates. It retrieves them by performing multiple http get requests to the Twitter API 2.0.

        Args: 
            keywords: list of keywords which have to be present in the tweets (retrieved if one keyword is inside the text).
            dates_range: tuple with start and end date; format: ("yyyy-mm-dd", "yyyy-mm-dd")
            filename: destination base-filename. 
            next_token: token for consecutive requests; can be found inside the previous tweet payload. If None, it starts from the first tweet. 
            max_requests: how many requests will be performed at max; if -1, the requests will continue till every tweet in the dates range is downloaded. 
            original_tweets: if True, retweets, quotes and replies will be filtered out. 
            verbose: if True, prints a "." everytime a request is performed correctly. 
        
        Raises:
            Exception: when http request isn't performed correctly. 
        """
        i = 0
        old_token = ''
        if next_token is None:
            # random string for the first file name
            next_token = '0000000000' + ''.join(random.choices(string.ascii_letters + string.digits, k=35))

        while next_token != old_token and i != max_requests:
            
            req = self.__http_request(keywords, dates_range, next_token, original_tweets)
            
            if req.status_code != 200:
                raise Exception('Http request failed. Response code: ' + str(req.status_code))

            if verbose:
                print('.', end='')

            name = filename + '_' + next_token + '.json'
            data = req.json()
            save_file(data, name)
            sleep(self.sleep_time)
            
            old_token = next_token
            if 'next_token' in data['meta']:
                next_token = data['meta']['next_token']

            i += 1



    def __http_request(self, keywords, dates_range, next_token, original_tweets):
        """
        Perform an http request to the Twitter API 2.0. 

        Args:
            keywords: list of keywords which have to be present in the tweets (retrieved if one keyword is inside the text).
            dates_range: tuple with start and end date, with format: ("yyyy-mm-dd", "yyyy-mm-dd"). 
            next_token: token for consecutive requests; can be found inside the previous tweet payload. 
            original_tweets: if True, retweets, quotes and replies will be filtered out. 

        Returns:
            The http request object. 
        """
        if type(keywords) == list:
            query = '(' + '%20OR%20'.join(['"' + x+'"' if ' ' in x else x for x in keywords]) + ')'
        else:
            query = keywords
        query += '%20lang%3A' + self.language
        
        if original_tweets:
             query += '%20-is%3Aretweet -is%3Aquote -is%3Areply'
        
        url = self.search_url + "?query=" + query
        if next_token[:10] != '0000000000':
            url += "&next_token=" + next_token
        url += "&start_time=" + dates_range[0] + 'T00:00:00.00Z'
        url += "&end_time=" + dates_range[1] + 'T00:00:00.00Z'
        url += "&tweet.fields=" + ','.join(self.tweet_fields)
        url += "&expansions=" + ','.join(self.expansions)
        url += "&user.fields=" + ','.join(self.user_fields)
        url += "&place.fields=" + ','.join(self.place_fields)
        url += "&max_results=" + self.max_results_per_request
        
        headers = {"Authorization": "Bearer "+BEARER_TOKEN}
        
        return requests.get(url, headers=headers)



    def download_tweet(self, tweet_id):
        """
        Download a single tweet given an id. 

        Args:
            tweet_id: id of the tweet. 

        Returns:
            The tweet as a dictionary. 
        """
        url = "https://api.twitter.com/2/tweets/" + str(tweet_id)
        headers = {"Authorization": "Bearer "+BEARER_TOKEN}
        return requests.get(url, headers=headers)




    #--------------------------------
    # merge and reformat functions
    #--------------------------------


    def merge_tweets_content(self, filenames, base_filename, fix_retweets_text=False):
        """
        Merge tweets from different requests into a single one, while fixing their format. 

        Args:
            filenames: list of the tweets filenames. 
            base_filename: base filename of the files.  
        """
        tweets = []
        for f in filenames:
            tmp = read_file(f)['data']
            for tweet in tmp:
                self.__fix_tweet(tweet)
            tweets += tmp
        if fix_retweets_text:
            tweets = self.__replace_retweets_text(tweets)
        save_file(tweets, base_filename+'_contents.json', 'json')



    def __fix_tweet(self, tweet):
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

        # flatten metrics
        for k,v in tweet['public_metrics'].items():
            tweet[k] = v
        del tweet['public_metrics']



    def __replace_retweets_text(self, tweets):
        """
        Replaces the truncated text of the retweets with the full text of the reference tweet. If the referenced tweet is not in the downloaded tweets, it retrieves it through the API. 

        Args:
            tweets: list of tweets. 

        Returns:
            The updated list of tweets. 
        """
        retweets = [tw for tw in tweets if is_retweet(tw)]
        referenced_ids = set([tw['referenced_tweets'][0]['id'] for tw in retweets])

        referenced_tweets = filter_list(tweets, 'id', referenced_ids, multiple=True)
        referenced_tweets = {x['id']:x['text'] for x in referenced_tweets} # reformat as dict

        absent_ids = referenced_ids.difference(set(referenced_tweets.keys()))

        # search for absent retweets
        d = {}
        for _id in absent_ids:
            req = self.download_tweet(_id)
            if req.status_code != 200:
                print('error:', req)
            else:
                d[_id] = req.json()['data']['text']
        
        # sleep for rate limit
        sleep(self.sleep_time)

        # merge dictionaries
        referenced_tweets = {**referenced_tweets, **d}

        # fix retweets text
        for tw in tweets:
            if is_retweet(tw):
                referenced_id = tw['referenced_tweets'][0]['id']
                if referenced_id in referenced_tweets:
                    tw['text'] = referenced_tweets[referenced_id]

        return tweets
            

            
    def merge_users_info(self, filenames, base_filename, geolocalize_locations=False):
        """
        Merge users information from different requests into a single one, while fixing their format, 
        meaning it flattens some fields, takes unique users, and geolocalizes their location. 

        Args:
            filenames: list of the tweets filenames. 
            base_filename: base filename of the files. 
        """
        # concatenate users
        users = []
        for f in filenames:
            users += read_file(f)['includes']['users']
        
        # set
        users = list({u['id']:u for u in users}.values())
        
        # flatten 
        for user in users:
            for k,v in user['public_metrics'].items():
                    user[k] = v
            del user['public_metrics']

        # geolocalization
        if geolocalize_locations:
            users = self.__geolocalize_users_locations(users)
        
        # save new file
        save_file(users, base_filename+'_users.json', 'json')



    def __geolocalize_users_locations(self, users):
        """
        Geolocalize the users location from the users list. 

        Args:
            users: list of users, where each user is a dictionary. 

        Returns:
            The same users list, with the location field geolocalized, if the place exists in Italy. 
        """
        df_italy_places = self.__get_italy_places()
        comuni_words = self.__get_italy_places_words(df_italy_places)
        regioni = self.__get_italy_regions(df_italy_places)

        data = {}
        for user in users:
            if 'location' in user:
                loc = user['location']
                loc = self.__normalize_location(loc)
                
                if loc is not None:
                    
                    if (loc not in data) and (self.__is_location_useful(loc, comuni_words)):
                        geo = self.geolocalize(loc, df_italy_places, regioni)
                        if geo is not None:
                            data[loc] = {'lat': geo[0], 'lon': geo[1], 'name': loc, 'region': geo[2]}

                    if loc in data:
                        user['location'] = data[loc]
        return users



    def merge_places(self, filenames, base_filename):
        """
        Merge tweets places from different requests into a single one, while fixing their format. 

        Args:
            filenames: list of the tweets filenames. 
            base_filename: base filename of the files. 
        """
        # concatenate places
        places = []
        for f in filenames:
            tmp = read_file(f)['includes']
            if 'places' in tmp:
                places += tmp['places']
        
        # set
        places = list({u['id']:u for u in places}.values())

        # flatten coordinates
        for p in places:
            p['bounding_box'] = p['geo']['bbox']
            del p['geo']

        # reformat
        places = self.__reformat_places(places)
        
        # save new file
        save_file(places, base_filename+'_places.json', _type='json')


    
    def __reformat_places(self, places):
        """
        Calculate coordinates from the place bounding box, filter out non-italian cities, separates name from region. 

        Args:
            places: list of places, where each place is a dictionary. 

        Returns:
            The formatted places list. 
        """
        df_italy_places = self.__get_italy_places()
        regions = self.__get_italy_regions(df_italy_places)

        places = [p for p in places if p['country'] == 'Italia' and p['place_type'] in ['city']]

        for p in places:
            p['lat'] = np.mean(p['bounding_box'][1::2])
            p['lon'] = np.mean(p['bounding_box'][::2])

            try:
                full_name = p['full_name'].split(', ')
                p['name'] = full_name[0]
                p['region'] = self.__fix_region(full_name[1])
            except:
                geo = self.geolocalize(p['full_name'], df_italy_places, regions)
                p['name'] = p['full_name']
                p['region'] = self.__fix_region(geo[2])
            
            for field in ['bounding_box', 'country', 'place_type', 'full_name']:
                del p[field]
            
        return places




    #--------------------------------
    # geolocalization functions
    #--------------------------------


    def geolocalize(self, location, italy_places, regions):
        """
        Geolocalize a location. If the location is not inside the list of places in Italy, then it performs a http request to Nominatim to geolocalize the address. 

        Args:
            location: address to be geolocalized. 
            italy_places: Pandas DataFrame containing every municipality in Italy, with their respective coordinates, province and region. 
            regions: set of regions. 

        Returns:
            A tuple containing the coordinates and the region of the location. 
        """
        match = self.__find_similar_match(location, italy_places)
        if match is None:
            match = self.__coords_http_request(location, regions)
        if match is not None:
            match[2] = self.__fix_region(match[2])
        return match



    def __get_italy_places(self):
        """
        Reads and return a file containing every municipality in Italy, with their province, province code, region, latitude and longitude. 

        Returns:
            A Pandas DataFrame with italian places. 
        """
        # Unione di:
        # CITTA'. https://github.com/MatteoHenryChinaski/Comuni-Italiani-2018-Sql-Json-excel/blob/master/italy_cities.xlsx
        # COORDINATE. https://github.com/MatteoHenryChinaski/Comuni-Italiani-2018-Sql-Json-excel/blob/master/italy_geo.xlsx
        # PROVINCE. https://gist.githubusercontent.com/LucaRosaldi/3081928/raw/02cd944c1ad4a24f5d6fcdaaf2a6b5889d712d8b/elenco_province_italiane_json_array.json
        italy_places = pd.read_csv('files/italy_places.csv')
        for c in ['municipality', 'province_code', 'province' ,'region']:
            italy_places[c] = italy_places[c].str.lower()
        return italy_places



    def __get_italy_regions(self, italy_places, alternative_names=True):
        """
        Returns a set of italian regions. 

        Args:
            italy_places: Pandas DataFrame containing every municipality in Italy, with their respective coordinates, province and region. 
            alternative_names: if True, adds to the set the alternative names of a few regions. 

        Returns:
            A set of regions. 
        """
        regions = set(italy_places['region'])
        if alternative_names:
            regions.add("valle d'aosta / vallée d'aoste")
            regions.add("trentino-alto adige/südtirol")
            regions.add("emilia romagna")
        return regions



    def __get_italy_places_words(self, italy_places):
        """
        Returns a set of words that appears in municipalities, province_codes, provinces and regions. 

        Args:
            italy_places: Pandas DataFrame containing every municipality in Italy, with their respective coordinates, province and region. 

        Returns:
            A set of words. 
        """
        df = italy_places.copy()
        df['region'] = df['region'].str.replace('/',' ').str.replace('-',' ')
        n = pd.concat([df[col] for col in ['municipality', 'province_code', 'province' ,'region']])
        n = ' '.join(n.dropna()).split()
        n = [x for x in n if len(x) > 3]
        return set(n)



    def __fix_region(self, region):
        """
        Fix the region format, by lowercasing it and replacing some alternative names. 

        Args:
            region: a string. 

        Returns:
            The reformatted region. 
        """
        region = region.lower()
        region = region.replace(" / vallée d'aoste", "")
        region = region.replace("/südtirol", "")
        region = region.replace("emilia romagna", "emilia-romagna")
        return region



    def __normalize_location(self, location):
        """
        Normalize a location, by lowercasing it, replacing english names, deleting non-letters characters. 

        Args:
            loc: a string. 

        Returns:
            The normalized location. 
        """
        # lowercase
        loc = location.lower()

        # keep letters, commas and whitesplaces
        loc = re.sub('[^a-z ,]+', '', loc)

        # not useful words
        loc = loc.replace('comune', ' ').replace('provincia', ' ').replace(' regione', ' ')
        loc = loc.replace('-', ' ').replace('_', ' ').replace(' ,', ',').replace(',,', ',')
        
        # regions translation
        loc = loc.replace('sicily', 'sicilia').replace('sardinia', 'sardegna').replace('lombardy', 'lombardia')
        loc = loc.replace('piedmont', 'piemonte').replace('tuscany', 'toscana')

        # delete consequent whitespaces
        loc = " ".join(loc.split())

        # delete non-letters at start and end of the location
        while len(loc) > 0 and not loc[0].isalpha():
            loc = loc[1:]
        while len(loc) > 0 and not loc[-1].isalpha():
            loc = loc[:-1]
        
        # not consider too short or too long locations
        if len(loc) < 3 or len(loc) > 100:
            loc = None
        
        return loc



    def __is_location_useful(self, location, places_words):
        """
        Determines if a location is useful, by checking if at least one word appear in a municipality, province_code, province or region. 

        Args:
            location: a string. 
            places_words: set of words that appears in municipalities, province_codes, provinces and regions. 
        
        Returns:   
            True if the intersection is not empty, False otherwise.  
        """
        intersection = set(location.replace(',',' ').split()).intersection(places_words)
        return len(intersection) > 0



    def __find_similar_match(self, location, italy_places):
        """
        Attempts to find a match between a location and the list of places in Italy. 

        Args:
            location: a string. 
            italy_places: Pandas DataFrame containing every municipality in Italy, with their province, province code, region, latitude and longitude. 

        Returns:
            Coordinates and region of the location if there is a match, None otherwise. 
        """
        # returns list of coords and region if match is found, else None
        italy_places = italy_places.copy()
        loc2 = location
        for word in ['italy', 'italia', 'europa', 'europe', ' ita ', ' eu ', ',']:
            loc2 = loc2.replace(word, ' ')
        loc2 = ' '.join(loc2.split())

        # removes from the string occurrences of regions, provinces or province codes
        data = {}
        for level in ['region', 'province', 'province_code']:
            intersection = set(loc2.split()).intersection(set(italy_places[level]))
            if len(intersection) == 1:
                italy_places = italy_places[italy_places[level]==list(intersection)[0]]
                data[level] = list(intersection)[0]
                loc2 = loc2.replace(data[level], '')
            if len(intersection) >= 2:
                break
        
        if len(intersection) <= 1:
            name = ' '.join(loc2.split()).strip()
            if name == '' and 'province' in data:
                name = data['province']

            # search for a match
            search = process.extractOne(name, italy_places['municipality'], scorer=fuzz.WRatio)
            if search is not None and search[1] >= 95:
                tmp = italy_places[italy_places['municipality']==search[0]]
                return list(tmp[['lat', 'lon', 'region']].iloc[0])
        
        return None



    def __coords_http_request(self, location, regions):
        """
        Performs a http request to Nominatim (OpenStreetMap open-source geocoder). 

        Args:
            location: a string. 
            regions: set of italian regions. 

        Returns:
            Coordinates and region of the location, if the request doesn't fail and the location is in Italy, None otherwise. 
        """
        url = f'https://nominatim.openstreetmap.org/search?q={location}&format=json'
        try:
            result = requests.get(url=url)
            result_json = result.json()
            if len(result_json) > 0:
                lat = float(result_json[0]['lat'])
                lon = float(result_json[0]['lon'])
                name = result_json[0]['display_name']
                if 'Italia' in name:
                    region = [reg for reg in regions if reg in name.lower()]
                    if len(region) > 0:
                        return [lat, lon, region[0]]
            return None
        except Exception as e: 
            print(e)
            return None

