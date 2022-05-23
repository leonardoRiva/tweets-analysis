import stanza
from TweetsUtils import *
import pandas as pd
import re
import numpy as np


class TweetsSentiment():


    def __init__(self):

        # lexicon data
        tmp = pd.read_csv('files/Italian-it-NRC-VAD-Lexicon_scaled (version 1).csv', sep=';', encoding='latin-1')
        tmp['Italian-it'] = tmp['Italian-it'].str.lower()
        del tmp['Word']
        tmp = tmp.groupby('Italian-it').mean()
        self.lex_dict = tmp.to_dict('index')

        # lexicon emojis 
        tmp = pd.read_excel('files/codici_emoji.xlsx', sheet_name='Emoji')
        tmp = tmp[['Twtr', 'Italian']].dropna()
        tmp.set_index('Twtr', inplace=True)
        self.emoji_dict = {k:v['Italian'] for k,v in tmp.to_dict('index').items()}



    def setup_stanza(self, lang='it'):
        stanza.download(lang) # download model
        self.nlp = stanza.Pipeline(lang, processors='lemma,tokenize,ner,mwt,pos') # initialize neural pipeline



    def replace_emojis(self, text):
        emojis_in_text = set(list(text)).intersection(set(self.emoji_dict.keys()))
        for emoji in emojis_in_text:
            text = text.replace(emoji, ' '+self.emoji_dict[emoji]+' ')
        text = ' '.join(text.split())
        return text



    def text_processing(self, text):
        # ADJ:   adjective
        # ADP:   adposition
        # ADV:   adverb
        # AUX:   auxiliary
        # CCONJ: coordinating conjunction
        # DET:   determiner
        # INTJ:  interjection
        # NOUN:  noun
        # NUM:   numeral
        # PART:  particle
        # PRON:  pronoun
        # PROPN: proper noun
        # PUNCT: punctuation
        # SCONJ: subordinating conjunction
        # SYM:   symbol
        # VERB:  verb
        # X:     other
        
        # remove URLs
        regex = r'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’]))'
        text = re.sub(regex, '', text).strip()
        
        # replace emojis
        text = self.replace_emojis(text)
        
        # remove html chars
        text = text
        for sequence in ['&gt', '&lt', '&amp', '...', '…']:
            text = text.replace(sequence, ' ')
        
        # tokenization, lemmatization, ner
        processed = self.nlp(text)
        
        # reformat entities
        entities = [e.to_dict() for e in processed.entities]
        entities = select_fields(entities, ['text', 'type'])
        
        # reformat text processing
        text_process = [select_fields(sentence, ['text', 'lemma', 'upos']) for sentence in processed.to_dict()]
        text_process = [word for sentence in text_process for word in sentence if ('lemma' in word) and ('upos' in word)]
        
        # remove stopwords, punctuation, numbers
        tags_to_delete = ['PUNCT', 'NUM', 'ADP', 'AUX', 'DET', 'CCONJ', 'SCONJ', 'PRON', 'X']
        text_process = [word for word in text_process 
                        if (word['upos'] not in tags_to_delete) and (not word['text'].startswith('@'))]
        
        return text_process, entities



    def calc_valence_arousal(self, words_list):
        val = []
        for word in words_list:
            w = word.lower().replace('#','')
            if w in self.lex_dict:
                val.append(self.lex_dict[w])
        valence = np.mean(select_fields(val, ['Valence'], as_list=True))
        arousal = np.mean(select_fields(val, ['Arousal'], as_list=True))
        return valence, arousal



    def classify_emotion(self, valence, arousal, v_threshold=0.3, a_threshold=0.3):
        emotion = 'neutral'

        if valence is not None and arousal is not None:
        
            if (valence > v_threshold) and (arousal < a_threshold) and (arousal > 0):
                emotion = 'joy'
                
            elif (valence > v_threshold) and (arousal > a_threshold):
                emotion = 'surprise'
                
            elif (valence > v_threshold) and (arousal > -a_threshold) and (arousal < 0):
                emotion = 'anticipation'
            
            elif (valence > v_threshold) and (arousal < -a_threshold):
                emotion = 'trust'
            
            elif (valence < -v_threshold) and (arousal < -a_threshold):
                emotion = 'sadness'
            
            elif (valence < -v_threshold) and (arousal > -a_threshold) and (arousal < 0):
                emotion = 'disgust'
            
            elif (valence < -v_threshold) and (arousal < a_threshold) and (arousal > 0):
                emotion = 'anger'
            
            elif (valence < -v_threshold) and (arousal > a_threshold):
                emotion = 'fear'
        
        return emotion



    def classify_sentiment(self, valence, v_threshold=0.3):
        sentiment = 'neutral'
        if valence is not None:
            if valence > v_threshold:
                sentiment = 'positive'
            elif valence < -v_threshold:
                sentiment = 'negative'
        return sentiment



    def process_tweet(self, text):
        text_process, entities = self.text_processing(text)

        lemmatized_words = [word['lemma'] for word in text_process]
        valence, arousal = self.calc_valence_arousal(lemmatized_words)
        emotion = self.classify_emotion(valence, arousal)
        sentiment = self.classify_sentiment(valence)
        
        return {
            'lemmatized_text': ' '.join(lemmatized_words), 
            'entities': entities, 
            'sentiment': sentiment, 
            'emotion': emotion, 
            'valence': valence, 
            'arousal': arousal
        }