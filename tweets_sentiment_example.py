# imports
from TweetsUtils import *
from TweetsSentiment import TweetsSentiment

# constants
PATH = 'c:/Users/myname/final_covid_tweets/'
FILENAME = 'covid_tweets_contents.json'
NEW_FILENAME = 'covid_tweets_contents_processed.json'

# read tweets
tweets = read_file(PATH + FILENAME)

# select non-duplicate texts
unique_texts = select_fields(tweets, ['text'], as_list=True, unique=True)

# perfrom sentiment analysis
ts = TweetsSentiment()
ts.setup_stanza()
d = {text: ts.process_tweet(text) for text in unique_texts}

# add sentiment to tweets
for i in range(len(tweets)):
    tw = tweets[i]
    if tw['text'] in d:
        tweets[i] = {**tw, **d[tw['text']]}

# save file
save_file(tweets, PATH + NEW_FILENAME)