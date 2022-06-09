
# tweets-analysis
Python pipeline for analyzing tweets. Tasks: download, text preprocessing, geolocalization, sentiment-emotion analysis, Named Entity Recognition. 


### Tweets download
``TweetsDownloader.py`` deals with downloading tweets. You need a ``credentials.py`` file, in the same format as ``credentials_example.py`` and in the same folder, with your Twitter API 2.0 keys with Academic Access. 

You will need to install the ``rapidfuzz`` library. 

Then, you can see the usage in ``tweets_download_example.py``. 


### Sentiment analysis 
``TweetsSentiment.py`` deals with performing a sentiment and emotion analysis, after the download. 

You will need to install the ``stanza`` library. 

Then, you can see the usage in ``tweets_sentiment_example.py``. 