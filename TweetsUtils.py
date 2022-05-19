
import pandas as pd
import numpy as np
import json


# returns the tweets that match the value in the field
# if value2 is not None, then it's a range between the two values
def filter_list(tweets, field, value, value2=None, multiple=False):
    if value2:
        return list(filter(lambda tw: (tw[field] >= value and tw[field] < value2), tweets))
    elif multiple:
        return list(filter(lambda tw: tw[field] in value, tweets))
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
                tmp = list(_flatten(tmp))
            tmp = list(set(tmp))
    
    elif unique and type(tmp[0]) == dict and 'id' in tmp[0]:
        tmp = unique_list_of_dicts(tmp)
    
    return tmp



def _flatten(l):
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



def filter_keywords(tweets, word, keywords):
    tmp_kw = keywords.copy()
    tmp_kw.remove(word)
    tmp_kw = set(tmp_kw)
    
    res = []
    for tw in tweets:
        s = set(tw['text'].lower().split())
        if word in s and len(s.intersection(tmp_kw)) >= 1:
            res.append(tw)
    return res



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



def read_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data