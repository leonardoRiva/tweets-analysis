
# tweets-analysis

Reading, cleaning, sentiment-emotion analysis, Named Entity Recognition


### Tweets download
``TweetsDownloader.py`` deals with downloading tweets. You need a ``credentials.py`` file, in the same format as ``credentials_example.py``, with your Twitter API 2.0 keys with Academic Access. 

To download tweets, you first need to define a set of keywords, a range of dates and a destination filename:
```python
keywords = ['covid', 'flu']
dates_range = ('2021-01-01', '2021-01-31')
filename = 'covid_tweets'
```
Then you can start downloading tweets:

```python
from TweetsDownloader import TweetsDownloader
td = TweetsDownloader(language='en', max_results_per_request=500, sleep_time=3)
td.download(keywords, dates_range, filename)
```

Finally, you can merge while reformatting the files from different requests. Note that this phase will create 3 different files, with the tweets, the users's information and the tweets geolocalizations. 
```python
import os
files = [f for f in os.listdir('./') if f.startswith(filename)]
td.merge_tweets(files, filename)
```
