import stanza
import pandas as pd
import numpy as np
import re

from TweetsUtils import *



class TweetsSentiment():
    """
    Sentiment and emotion analysis of tweets. 
    """


    def __init__(self):
        """
        Class initialization. It initializes the dictonaries for retrieving words and emojis valence/arousal. 
        """
        # lexicon
        tmp = pd.read_csv('files/Italian-it-NRC-VAD-Lexicon_scaled (version 1).csv', sep=';', encoding='latin-1')
        tmp['Italian-it'] = tmp['Italian-it'].str.lower()
        del tmp['Word']
        tmp = tmp.groupby('Italian-it').mean()
        self.lex_dict = tmp.to_dict('index')

        # emojis 
        tmp = pd.read_excel('files/codici_emoji.xlsx', sheet_name='Emoji')
        tmp = tmp[['Twtr', 'Italian']].dropna()
        tmp.set_index('Twtr', inplace=True)
        self.emoji_dict = {k:v['Italian'] for k,v in tmp.to_dict('index').items()}



    def setup_stanza(self, language='it'):
        """
        Download Stanza model for the selected language and initialize the pipeline for lemmatization, tokenization, NER, MWT and POS tagging. 

        Args: 
            lang: two-letters country code.
        """
        stanza.download(language)
        self.nlp = stanza.Pipeline(language, processors='lemma,tokenize,ner,mwt,pos')



    def process_tweet(self, text):
        """
        Perform the full processing of the text and calculates sentiment and emotion. 

        Args:
            text: text of the tweet. 

        Returns:
            A dictionary with the result of the processing. 
        """
        text_process, entities = self.__text_processing(text)

        lemmatized_words = [word['lemma'] for word in text_process]
        valence, arousal = self.__calc_valence_arousal(lemmatized_words)
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



    def __replace_emojis(self, text):
        """
        Replaces every emoji in the text with its meaning, if the emojij is in the emojis file. 

        Args:
            text: text of the tweet. 

        Returns:
            The text with replaces emojis. 
        """
        emojis_in_text = set(list(text)).intersection(set(self.emoji_dict.keys()))
        for emoji in emojis_in_text:
            text = text.replace(emoji, ' '+self.emoji_dict[emoji]+' ')
        return ' '.join(text.split())



    def __text_processing(self, text):
        """
        Process the text by cleaning it and performing NLP tasks. 

        Args:
            text: string to be processed. 

        Returns:
            The processed text (with POS, lemma fields) and the entities. 
        """
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
        text = self.__replace_emojis(text)
        
        # remove html chars
        for sequence in ['&gt', '&lt', '&amp', '...', '…']:
            text = text.replace(sequence, ' ')
        text = text.encode("utf-8", "ignore").decode()
        
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



    def __calc_valence_arousal(self, words_list):
        """
        Calculates valence and arousal of a list of words, by averaging each of their valence and arousal. 

        Args:
            words_list: list of words. 

        Returns:
            Average valence and arousal. 
        """
        val = []
        for word in words_list:
            w = word.lower().replace('#','')
            if w in self.lex_dict:
                val.append(self.lex_dict[w])
        valence = np.mean(select_fields(val, ['Valence'], as_list=True))
        arousal = np.mean(select_fields(val, ['Arousal'], as_list=True))
        return valence, arousal



    def classify_emotion(self, valence, arousal, v_threshold=0.3, a_threshold=0.3):
        """
        Classify the emotion on the text, based on its valence and arousal (from Plutchik's wheel of emotions). 

        Args:
            valence: valence of the tweet. 
            arousal: arousal of the tweet. 
            v_threshold: threshold for the valence value. 
            a_threshold: threshold for the arousal value. 

        Returns:
            The emotion. 
        """
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
        """
        Classify the sentiment on the text, based on its valence. 

        Args:
            valence: valence of the tweet. 
            v_threshold: threshold for the valence value. 

        Returns:
            The sentiment (negative, neutral or positive). 
        """
        sentiment = 'neutral'
        if valence is not None:
            if valence > v_threshold:
                sentiment = 'positive'
            elif valence < -v_threshold:
                sentiment = 'negative'
        return sentiment

