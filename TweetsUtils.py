import pandas as pd
import numpy as np
import json



def filter_year(tweets, year):
    if type(tweets[0]['datetime']) == str:
        return [tw for tw in tweets if tw['datetime'].startswith(str(year))]
    else:
        return [tw for tw in tweets if tw['datetime'].year == year]


# returns the tweets that match the value in the field
# if value2 is not None, then it's a range between the two values
def filter_list(tweets, field, value, value2=None, multiple=False):
    if value2:
        return list(filter(lambda tw: (tw[field] >= value and tw[field] < value2), tweets))
    elif multiple:
        return list(filter(lambda tw: tw[field] in value, tweets))
    elif field == 'hashtags':
        return [tw.copy() for tw in tweets if 'hashtags' in tw and value.lower() in [x.lower() for x in tw['hashtags']]]
    elif field == 'entities':
        return [tw.copy() for tw in tweets if 'entities' in tw and value.lower() in [x['text'].lower() for x in tw['entities']]]
    else:
        return list(filter(lambda tw: tw[field] == value, tweets))



# return the sorted tweets by the field
def sort_list(tweets, by, reverse=True):
    return sorted(tweets, key=lambda tw: tw[by], reverse=reverse)



# returns the tweets with the selected fields 
def select_fields(tweets, fields, as_list=False, unique=False):
    tmp = [{k: tw[k] for k in tw.keys() & set(fields)} for tw in tweets]
    
    if as_list:
        tmp = [list(x.values()) for x in tmp]
        
        if np.sum([len(x) for x in tmp]) == len(tmp): # if items of length 1, flatten
            tmp = [item for sublist in tmp for item in sublist] 
        
        if unique:
            if type(tmp[0]) == list:
                tmp = list(flatten(tmp))
            tmp = list(set(tmp))
    
    elif unique and type(tmp[0]) == dict and 'id' in tmp[0]:
        tmp = unique_list_of_dicts(tmp)
    
    return tmp



def flatten(l):
    for el in l:
        if isinstance(el, Iterable) and not isinstance(el, (str, bytes)):
            yield from _flatten(el)
        else:
            yield el
            

            
def unique_list_of_dicts(l, by='id'):
    return list({v[by]:v for v in l}.values())



# count how many tweets for each category of the field
def count_list(tweets, field):
    return pd.value_counts([tw[field] for tw in tweets])



# check if a tweet is a retweet
def is_retweet(tweet):
    if 'referenced_tweets' in tweet:
        for reference in tweet['referenced_tweets']:
            if reference['type'] == 'retweeted':
                return reference['id']
    return False



# counts how many keywords are present in a text
def count_keywords(text, keywords):
    return np.sum([k in text for k in keywords])



# returns tweets with the keyword k, in combination with other (n-1) keywords
def keyword_in_combination(tweets, k, keywords, n):
    tmp = [tw for tw in tweets if k in tw['text'].lower()]
    return [tw for tw in tmp if count_keywords(tw['text'], keywords) >= n]



# get list of mentions (with @) in a text
def get_mentions(text):
    return [x.replace('.','').replace(',','').replace(';','').replace('?','').replace('!','') 
            for x in text.split() if x.startswith('@')]



# check if a text contains a mention
def has_mentions(text, all_mentions):
    mentions = set(get_mentions(text))
    return len(mentions.intersection(all_mentions)) > 0



# as a dataframe
def get_tweets_with_location(tweets, users, places):
    # get data
    tmp = select_fields(tweets, ['datetime', 'text', 'geo', 'author_id'])
    df = pd.DataFrame(tmp)
    
    # geolocalization
    df_geo = df.copy().dropna()
    df_geo['geo'] = df_geo['geo'].apply(lambda x: x['place_id'])
    place_ids = select_fields(places, ['id'], as_list=True, unique=True)
    df_geo = df_geo[df_geo['geo'].isin(place_ids)].reset_index(drop=True)
    rows = []
    for g in df_geo['geo']:
        rows += filter_list(places, 'id', g)
    tmp = pd.DataFrame(rows).reset_index(drop=True)
    df_geo = pd.concat([df_geo, tmp], axis=1)
    for field in ['geo', 'id']:
        del df_geo[field]

    # user location
    df_loc = df[df['geo'].isna()].copy()
    del df_loc['geo']
    d = {u['id']:u['location'] for u in users if ('location' in u) and (type(u['location'])==dict)}
    df_loc['author_id'] = df_loc['author_id'].apply(lambda x: d[x] if x in d else None)
    df_loc = df_loc.dropna().reset_index(drop=True)
    tmp = pd.DataFrame(list(df_loc['author_id']))
    df_loc = pd.concat([df_loc, tmp], axis=1)

    # add row type
    df_geo['type'] = ['geolocalization'] * len(df_geo)
    df_loc['type'] = ['user_location'] * len(df_loc)
    
    # combination
    df = pd.concat([df_geo, df_loc], axis=0)
    df = df.sort_values(by='datetime')
    del df['author_id']
    
    return df



#--------------------------------
# read and write functions
#--------------------------------


def read_file(filename):
    """
    Read a json file 

    Args:
        filename: name of the json file. 

    Returns:
        A dictionary containing the tweets. 
    """
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data



def save_file(text, filename, _type='json'):
    """
    Write a dictionary into a json file. 

    Args:
        filename: name of the json file. 
        _type: format of the destination file, either "txt" or "json"
    """
    if _type == 'txt':
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(text)
    elif _type == 'json':
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(text, f)
