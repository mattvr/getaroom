import random
import json
import math
from datetime import datetime
import httplib, urllib
import logging as logger

from rate_limit_service import  is_rate_limited
from config import WIT_ACCESS_TOKEN, NEXMO_API_KEY, NEXMO_API_SECRET, NEXMO_PHONE_NO, LOGGER_SERVER, SQLITE_DATABASE, DEBUG_SMS, BLACKLIST
from getaroom import get_available_rooms
from dictionary import get_phrase

# External dependencies
from flask import Flask, request
from nexmomessage import NexmoMessage # pip install -e git+https://github.com/marcuz/libpynexmo.git#egg=nexmomessage

app = Flask(__name__)
ban_lookup = json.loads(open(BLACKLIST).read())

logger.basicConfig(filename=LOGGER_SERVER,level=logger.DEBUG)
@app.route('/getaroom', methods=['GET', 'POST'])
def getaroom():
    sender_no = request.values.get('msisdn')
    body = request.values.get('text')

    if is_banned(sender_no):
        logger.warn("Number banned! - %s - %s", (body, sender_no))
        return "Number banned"

    if sender_no is None or body is None:
        return 'Invalid message.'

    logger.info("Received request - %s - %s" % (body, sender_no))

    # TODO: account for concatenated & unicode messages
    wit_response = send_to_wit(body)
    sms_response = parse_response(json.loads(wit_response))
    ret_val = ""

    if is_rate_limited(sender_no, num_texts=1.0):
        logger.warn("Phone number is rate limited (%s)" % sender_no)
        return "Phone number is rate limited. Try again later."
    else:
        if DEBUG_SMS:
            print("SMS DEBUG:\n%s\nfrom: %s\n===========" % (sms_response, sender_no))
        else:
            send_sms(sender_no, sms_response)
        print wit_response

        ret_val = sms_response
    return ret_val

def send_to_wit(message):
    conn = httplib.HTTPSConnection('api.wit.ai')
    headers = {'Authorization': 'Bearer %s' % (WIT_ACCESS_TOKEN,)}
    params = urllib.urlencode({'v': '20141022', 'q': message})
    url = '/message?%s' % (params,)
    conn.request('GET', url, '', headers)
    response = conn.getresponse()
    return response.read()

def parse_response(response):
    intent =  response['outcomes'][0]['intent']
    if intent == 'getaroom':
        return parse_getaroom(response)
    elif intent == 'help':
        return get_phrase("HELP")
    elif intent == 'stop':
        return parse_joke(response)
    else:
        return 'Invalid message. Try "get a room in TORG"'

def parse_getaroom(response):
    if 'outcomes' in response and len(response['outcomes']) > 0:
        outcome = response['outcomes'][0]
        if 'entities' in outcome and len(outcome['entities']) > 0:
            entity = outcome['entities']
            if 'building' in entity and len(entity['building']) > 0:
                building = entity['building'][0]['value']

                rooms = get_available_rooms(building, datetime.now())
                if len(rooms) == 0:
                    return get_phrase("NO_ROOMS")
                else:
                    building_name = rooms[0].building_name
                    string = ''
                    if len(rooms) == 1:
                        phrase = get_phrase("ONE_ROOM")
                        string += phrase % (building_name,)
                    elif len(rooms) <= 3:
                        phrase = get_phrase("SEVERAL_ROOMS")
                        string += phrase % (len(rooms), building_name)
                    else:
                        phrase = get_phrase("SEVERAL_MORE_ROOMS")
                        string += phrase % (building_name,)

                iterations = min((3, len(rooms)))
                for i, room in enumerate(rooms[:iterations]):
                    if not room.end_availability:
                        string += '- %s %s (rest of day)' % (room.building_code, room.number)
                    else:
                        string += '- %s %s (until %s)' % (room.building_code, room.number, room.end_availability)
                    if i is not iterations - 1:
                        string += '\n'

                numTexts = math.floor(1 + (len(string) / 160)) # this is the number of texts sent
                logger.info("SMS Response Generated - consumes %d SMS" % numTexts)
                print("SMS Response Generated - consumes %d SMS" % numTexts)
                return string
    return get_phrase("INVALID_MESSAGE")

def is_banned(number):
    bans = ban_lookup['bans']
    if number in bans:
        return True
    return False

def parse_joke(response):
    string = get_phrase("PENGUIN_FACTS_WELCOME")
    facts = get_phrase("PENGUIN_FACTS")
    string += random.choice(facts)
    return string

def send_sms(number, message):
    msg = {
        'reqtype'   : 'json',
        'api_key'   : NEXMO_API_KEY,
        'api_secret': NEXMO_API_SECRET,
        'from'      : NEXMO_PHONE_NO,
        'to'        : number,
        'text'      : message
    }
    sms = NexmoMessage(msg)
    sms.set_text_info(msg['text'])
    response = sms.send_request()
    if not response:
        logger.error("[NEXMO] Failed to send response: %s [to] %s" % (message, number))
        print "Failed to send response"

if __name__ == "__main__":
    app.run(host='0.0.0.0')
