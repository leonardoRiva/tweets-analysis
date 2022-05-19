
# tweets-analysis

Reading, cleaning, sentiment-emotion analysis, Named Entity Recognition, ...


### Tweets download
``TweetsDownloader.py`` deals with downloading tweets. You need a ``credentials.py`` file, in the same format as ``credentials_example.py`` and in the same folder, with your Twitter API 2.0 keys with Academic Access. 

First, you need to install rapidfuzz library:

```python
pip install rapidfuzz
```

Then, you need to define a set of keywords, a range of dates and a destination filename:
```python
keywords = ['covid', 'flu']
dates_range = ('2021-01-01', '2021-01-31')
filename = 'covid_tweets'
```
After that, you can start downloading tweets:

```python
from TweetsDownloader import TweetsDownloader
td = TweetsDownloader(language='en', max_results_per_request=500, sleep_time=2)
td.download(keywords, dates_range, filename)
```

Finally, you can merge while reformatting the files from different requests. Note that this phase will create 3 different files, with the tweets, the users's information and the tweets geolocalizations. Keep in mind that the ``merge_users_info`` function needs to perform multiple requests to geolocalize locations and is relatively slow. 

```python
import os
files = [f for f in os.listdir('./') if f.startswith(filename)]
td.merge_tweets_content(files, filename)
td.merge_users_info(files, filename)
td.merge_places(files, filename)
```


### Flu analysis 
``analysis_flu.ipynb`` deals with analyzing the downloaded data...