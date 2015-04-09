import json
import math
from datetime import datetime
import httplib, urllib
import logging as logger
import dateutil.parser #pip install python-dateutil

from rate_limit_service import is_rate_limited, is_banned
from config import WIT_ACCESS_TOKEN, NEXMO_API_KEY, NEXMO_API_SECRET, NEXMO_PHONE_NO, LOGGER_SERVER, DEBUG_SMS, SMS_LARGE_PENALTY, LOG_MESSAGES
from getaroom import get_available_rooms
from dictionary import get_phrase
from message_logger import log_message, MessageDirection

# External dependencies
from flask import Flask, request
from nexmomessage import NexmoMessage # pip install -e git+https://github.com/marcuz/libpynexmo.git#egg=nexmomessage

app = Flask(__name__)

logger.basicConfig(filename=LOGGER_SERVER,level=logger.DEBUG)
@app.route('/getaroom', methods=['GET', 'POST'])
def getaroom():
    sender_no = request.values.get('msisdn')
    body = request.values.get('text')

    if sender_no is None or body is None:
        logger.error("RECEIVED INVALID MESSAGE.")
        return 'Invalid message.'

    if LOG_MESSAGES:
        log_message(sender_no, body, MessageDirection.INBOUND)

    if is_banned(sender_no):
        logger.warn("Number banned! - %s - %s", (body, sender_no))
        return "Number banned"

    logger.info("Received request - %s - %s" % (body, sender_no))

    # TODO: account for concatenated & unicode messages
    wit_response = send_to_wit(body)
    sms_response = parse_response(json.loads(wit_response))

    num_texts = math.floor(1 + (len(sms_response) / 160)) # this is the number of texts sent
    logger.info("SMS Response Generated - consumes %d SMS" % num_texts)
    print("SMS Response Generated - consumes %d SMS" % num_texts)

    sms_penalty = 1.0
    if SMS_LARGE_PENALTY:
        sms_penalty = float(num_texts)

    if is_rate_limited(sender_no, num_texts=sms_penalty):
        logger.warn("Phone number is rate limited (%s)" % sender_no)
        return "Phone number is rate limited. Try again later."
    else:
        if DEBUG_SMS:
            print("SMS DEBUG:\n%s\nfrom: %s\n===========" % (sms_response, sender_no))
        else:
            send_sms(sender_no, sms_response)
        print wit_response

        return sms_response

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
            entities = outcome['entities']
            if 'building' in entities and len(entities['building']) > 0:
                building = entities['building'][0]['value']
                time = datetime.now()

                if 'datetime' in entities and len (entities['datetime']) > 0:
                    time_str = entities['datetime'][0]['value']
                    time = dateutil.parser.parse(time_str)

                rooms = get_available_rooms(building, time)
                if len(rooms) == 0:
                    return get_phrase("NO_ROOMS")
                else:
                    building_name = rooms[0].building_name
                    string = ''
                    salutation = get_phrase("INTRO")
                    if len(rooms) == 1:
                        phrase = "%s %s" % (salutation, get_phrase("ONE_ROOM"))
                        string += phrase % (building_name,)
                    elif len(rooms) <= 3:
                        phrase = "%s %s" % (salutation, get_phrase("SEVERAL_ROOMS"))
                        string += phrase % (len(rooms), building_name)
                    else:
                        phrase = "%s %s" % (salutation, get_phrase("SEVERAL_MORE_ROOMS"))
                        string += phrase % (building_name,)

                iterations = min((3, len(rooms)))
                for i, room in enumerate(rooms[:iterations]):
                    if not room.end_availability:
                        string += '- %s %s (rest of day)' % (room.building_code, room.number)
                    else:
                        string += '- %s %s (until %s)' % (room.building_code, room.number, room.end_availability)
                    if i is not iterations - 1:
                        string += '\n'

                return string
    return get_phrase("INVALID_MESSAGE")


def parse_joke(response):
    string = get_phrase("PENGUIN_FACTS_WELCOME")
    fact = get_phrase("PENGUIN_FACTS")
    string += fact
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

    if LOG_MESSAGES:
        log_message(number, message, MessageDirection.OUTBOUND)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
