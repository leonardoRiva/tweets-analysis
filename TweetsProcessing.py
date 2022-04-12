
import pandas as pd
import numpy as np
import re
import string
from nltk.corpus import stopwords
from string import punctuation
import stanza



EMOTIONS = ['anger', 'sadness', 'fear', 'disgust', 'neutral', 'anticipation', 'joy', 'surprise', 'trust']
SENTIMENTS = ['negative', 'neutral', 'positive']

# ner
stanza.download('it') # download model
nlp = stanza.Pipeline('it', processors='lemma,tokenize,ner') # initialize neural pipeline

# lexicon data
lex = pd.read_csv('lexicon_en_it.csv', sep=';', encoding='latin-1')
lex_emoji = pd.read_excel('lexicon_emoji.xlsx', sheet_name='emoji')

# stopwords
stopwords_list = stopwords.words('italian')
stopwords_list.append('avere')
stopwords_list.append('essere')




def get_extended_language(lang):
    lang_dict = {'it': 'italian', 'en': 'english'}
    return lang_dict[lang]


def get_emojis(text):
    """
    Given a raw text, it return the list of emojis it contains. 

    Parameters
    ----------
    text : string
        The tweet's raw text.

    Returns
    -------
    emojis : list
        List of emojis inside the text. 

    """

    # regex for emoji identification
    EMOJI_PATTERN = re.compile(
        "(["
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        u"\u2640-\u2642"
        u"\u2600-\u2B55"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\u3030"
        "])"
    )
    emojis = re.findall(EMOJI_PATTERN, text)
    return emojis


def clean_text(text, language, topic_words=[]):

    # remove URLs
    text = re.sub('(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)', '', text) 

    # lemmatization and NER
    text, entities = stanza_process(text)

    # remove usernames
    text = re.sub('@[^\s]+', '', text) 

    # fix quote problem
    text = re.sub('\W+', ' ', text) 

    # remove punctuation
    text_lc = "".join([word.lower() for word in text if word not in punctuation]) 

    # remove numbers
    text_rc = re.sub('[0-9]+', '', text_lc)

    # fix ampersand
    text_rc = text_rc.replace('&amp', '&')

    # tokenization
    tokens = re.split('\W+', text_rc) 

    # remove stopwords
    text = [word for word in tokens if word not in stopwords_list and len(word) > 1] 

    # remove topic words
    text = [word for word in text if word not in topic_words]

    return text, entities


def stanza_process(text):
    process = nlp(text)
    text = ' '.join([w['lemma'] for w in process.to_dict()[0] if 'lemma' in w])

    entities = []
    for e in process.entities:
        entities.append({'text': e.text, 'type': e.type})
    
    return text, entities


def calculate_text_values(text, emojis, language):
    """
    It analyzes the text and calculates its valence and arousal. It also takes
    into account emojis, which are converted to text. 

    Returns
    -------
    None.

    """

    # Replaces emojis with one or more words, which represent their meaning. 
    # These words are then appended to the text. 
    for em in emojis:
        word_em = lex_emoji.loc[lex_emoji['code'] == 'U+{:X}'.format(ord(em)), language]
        if not word_em.empty and type(word_em.item()) == str:
            text.append(word_em.item().strip())

    # Calculates valence and arousal for each word. If if finds more than 
    # one occurrence in the lexicon, it averages the results. 
    w_values = [calculate_word_values(word, language) for word in text]
    new_df = pd.DataFrame(w_values, columns=['valence', 'arousal'])
    new_df = new_df.dropna()
    
    # If at least one occurrence was found, it averages every value of valence
    #  and arousal. 
    if new_df.empty:
        return None, None
    
    valence = new_df['valence'].values.mean()
    arousal = new_df['arousal'].values.mean()
    return valence, arousal


def calculate_word_values(word, language):
    """
    Given a word, it calculates its valence and arousal. If the 
    word is not in the lexicon, it attempts to find it using its lemma. 

    Parameters
    ----------
    word : string
        Word to be analyzed.

    Returns
    -------
    valence : double
        Valence of the word. 
    arousal : double
        Arousal of the word. 

    """

    element = lex.loc[lex[language+'_lemma'].str.strip() == word,]
    if element.empty:
        return None, None

    valence = element['valence'].values.mean()
    arousal = element['arousal'].values.mean()    
    
    if valence is None or arousal is None:
        return None, None
    
    return valence, arousal


def classify_emotion(valence, arousal, valence_t=0.4, arousal_t=0.4):
    """
    Determines the sentiment, based on valence and arousal.

    Returns 
    -------
    emotion : string
        Sentiment of the text

    """
    if valence is None or arousal is None:
        return "neutral"


    if valence > valence_t and arousal < arousal_t and arousal > 0:
        emotion = "joy"

    elif valence > valence_t and arousal > arousal_t:
        emotion = "surprise"

    elif valence > valence_t and arousal > -arousal_t and arousal < 0:
        emotion = "anticipation"

    elif valence > valence_t and arousal < -arousal_t:
        emotion = "trust"

    elif valence < -valence_t and arousal < -arousal_t:
        emotion = "sadness"

    elif valence < -valence_t and arousal < 0 and arousal > -arousal_t:
        emotion = "disgust"

    elif valence < -valence_t and arousal > 0 and arousal < arousal_t:
        emotion = "anger"

    elif valence < -valence_t and arousal > arousal_t:
        emotion = "fear"

    else:
        emotion = "neutral"

    return emotion


def classify_sentiment(valence, lower_t=-0.4, upper_t=0.4):
    sentiment = 'neutral'
    if valence is not None:
        if valence > upper_t:
            sentiment = 'positive'
        elif valence < lower_t:
            sentiment = 'negative'
    return sentiment


def process_tweet(full_text, language, topic_words):
    emojis = get_emojis(full_text)
    text, entities = clean_text(full_text, language, topic_words)

    valence, arousal = calculate_text_values(text, emojis, language)

    return {
        'text': ' '.join(text + emojis), 
        'entities': entities, 
        'valence': valence, 
        'arousal': arousal, 
        'emotion': classify_emotion(valence, arousal), 
        'sentiment': classify_sentiment(valence)
    }




# ------------------------------
# FUNCTIONS FOR RETRIEVING INFO
# ------------------------------


def get_field(tweets, field):
    return [tw[field] for tw in tweets]


def get_fields(tweets, fields, as_df=False):
    data = [get_field(tweets, f) for f in fields]
    if as_df:
        tmp = pd.DataFrame(data).T
        tmp.columns = fields
        return tmp
    return data


def get_tweets(tweets, field, name):
    if field == 'entities':
        return [tw for tw in tweets if name in [e['text'] for e in tw['entities']]]
    if field == 'hashtags':
        return [tw for tw in tweets if name in tw['hashtags']]
    return [tw for tw in tweets if tw[field]==name]


def get_list(tweets, field, unique=True):
    l = [tw[field] for tw in tweets]# if tw[field] is not None]
    if field == 'hashtags' or field == 'entities':
        l = [item for sublist in l for item in sublist] #flatten
    if field == 'entities':
        l = [x['text'] for x in l]
    if unique:
        l = list(set(l))
    return l


def get_count_by_time(tweets, field, rate, normalize=False):
    time = get_field(tweets, 'time')
    series = get_field(tweets, field)
    dummies = pd.get_dummies(pd.Series(series, index=time))
    dummies.index = pd.to_datetime(dummies.index)
    s = dummies.resample(rate).sum()
    if normalize:
        s = s.div(s.sum(axis=1), axis=0)
        s = s.fillna(0.0)   
    return s


def get_stats(tweets):
    stats = {}
    stats['count'] = len(tweets)
    stats['avg_retweets'] = get_avg_field_value(tweets, 'retweets')
    stats['valence'] = get_list(tweets, 'valence', unique=False)
    stats['arousal'] = get_list(tweets, 'arousal', unique=False)
    stats['texts'] = get_list(tweets, 'full_text', unique=False)
    stats['emotion_count'] = get_sent_count(tweets, 'emotion')
    stats['sentiment_count'] = get_sent_count(tweets, 'sentiment')
    return stats


def get_sent_count(tweets, field):
    var_list = EMOTIONS
    if field == 'sentiment': 
        var_list = SENTIMENTS
    counts = {x: 0 for x in var_list}
    for em in [tw[field] for tw in tweets]:
        counts[em] += 1
    return counts


def get_user_bio(tweets, username):
    for tw in tweets:
        if tw['user_name'] == username:
            return (tw['user_location'], tw['user_followers'])
    return None

