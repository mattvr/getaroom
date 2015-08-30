import json
import random
import config

dictionary = json.loads(open(config.DICTIONARY_FILE).read())

def get_phrase(key, language=config.DEFAULT_LANGUAGE):
    try:
        dict_lang = dictionary[language]['phrases']
        val = dict_lang[key]
        if isinstance(val, list):
            return random.choice(val)
        return val
    except:
        return False