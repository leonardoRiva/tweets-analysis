
# tweets-analysis
Python pipeline for analyzing tweets. Tasks: download, text preprocessing, geolocalization, Sentiment Analysis, Named Entity Recognition. 


### Tweets download
``TweetsDownloader.py`` deals with downloading tweets. You need a ``credentials.py`` file, in the same format as ``credentials_example.py`` (in the examples folder), with your Twitter API 2.0 keys with Academic Access. 

You will need to install the ``rapidfuzz`` library. 


### Examples
You can see the usage of each functionality to the ``examples`` folder. Keep in mind that, in order to use those file, you need to move them in the main folder, with the other files. 