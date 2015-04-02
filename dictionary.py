import json
import random
from config import DICTIONARY_FILE, DEFAULT_LANGUAGE

dictionary = json.loads(open(DICTIONARY_FILE).read())

def get_phrase(key, language=DEFAULT_LANGUAGE):
    try:
        dict_lang = dictionary[language]['phrases']
        val = dict_lang[key]
        if isinstance(val, list):
            return random.choice(val)
        return val
    except:
        return False