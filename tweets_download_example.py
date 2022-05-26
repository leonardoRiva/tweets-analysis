# import
from TweetsDownloader import TweetsDownloader

# constants
FILENAME = 'covid_tweets'
PATH = 'c:/Users/myname/Downloads/'
DEST_PATH = 'c:/Users/myname/final_covid_tweets/'
KEYWORDS = ['covid', 'coronavirus']
DATES_RANGE = ('2020-03-01', '2020-03-08')
LANGUAGE = 'en'

# download data
td = TweetsDownloader(language=LANGUAGE, max_results_per_request=500, sleep_time=2, filename=FILENAME, path=PATH)
td.download(KEYWORDS, DATES_RANGE, original_tweets=False)

# merge files
td.merge_tweets_content(destination_path=DEST_PATH, fix_retweets_text=False)
td.merge_users_info(destination_path=DEST_PATH, geolocalize_locations=False)
td.merge_places(destination_path=DEST_PATH)

