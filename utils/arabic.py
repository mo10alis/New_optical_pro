import arabic_reshaper
from bidi.algorithm import get_display

def ar(text):
    try:
        text = str(text)
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except:
        return text