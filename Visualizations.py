from matplotlib import pyplot as plt
from wordcloud import WordCloud
import string
import pandas as pd
import os



def wordcloud(freq, size=(7,5)):
    plt.rcParams["figure.figsize"] = size

    # the regex used to detect words is a combination of normal words, ascii art, and emojis
    normal_word = r"(?:\w[\w']+)"
    ascii_art = r"(?:[{punctuation}][{punctuation}]+)".format(punctuation=string.punctuation)
    emoji = r"(?:[^\s])(?<![\w{ascii_printable}])".format(ascii_printable=string.printable)
    regexp = r"{normal_word}|{ascii_art}|{emoji}".format(normal_word=normal_word, ascii_art=ascii_art, emoji=emoji)

    d = path.dirname(__file__) if "__file__" in locals() else os.getcwd()
    font_path = os.path.join(d, 'fonts', 'Symbola', 'Symbola.ttf')

    wc = WordCloud(font_path=font_path, regexp=regexp, background_color="white")
    wc.generate_from_frequencies(freq)
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.show()



def stackplot(s, size=(8,5)):
    plt.rcParams["figure.figsize"] = size
    plt.stackplot(s.index, s.values.T, labels=s.columns)
    plt.legend(loc='upper right')
    plt.xticks(rotation=-45)
    plt.plot()
    plt.show()


