from datetime import datetime
import httplib
import urllib
import logging as logger
import json
import operator
import math
import time

import config

from getaroom import get_available_rooms
import dictionary
from message_logger import log_message, MessageDirection
import rate_limit_service
from utils import bcolors, get_terminal_size

# External dependencies
import dateutil.parser
from nexmomessage import NexmoMessage
import emoji

allowed_types = ['text']

def print_task_info(body, num_texts, rate_limit_end, rate_limited, sender_no, sms_response, success):
    t = time.strftime('%I:%m:%S %p %d/%m/%y')
    (w, h) = get_terminal_size()
    num = math.floor(w / 2)
    if success:
        print "=" * (int(num - 3)),
        print(bcolors.OKGREEN + " OK " + bcolors.ENDC),
        print "=" * (int(num - 3))
    else:
        print "=" * (int(num - 3)),
        print(bcolors.FAIL + "FAIL" + bcolors.ENDC),
        print "=" * (int(num - 3))
    print(
        "[%s] SMS Response :: " % (t, ) + bcolors.OKBLUE + " %s " % (sender_no, ) + bcolors.ENDC + " :: consumes %d" % (
            num_texts, ))
    if rate_limited: print("Phone number is rate limited (%s) until %s" % (sender_no, rate_limit_end))
    print("IN : %s" % body)
    print("OUT: %s" % sms_response)
    print "=" * w


def parse_sms_main(body, sender_no, encoding = u'text'):
    wit_response = None

    if encoding == u"unicode":
        sms_response = parse_unicode(body)
    else:
        if encoding not in allowed_types:
            print "Invalid message received"
            return "Invalid message"
        wit_response = send_to_wit(body)
        sms_response = parse_response(json.loads(wit_response))
    success = True
    if isinstance(sms_response, tuple):
        success = sms_response[0]
        sms_response = sms_response[1]


    num_texts = math.floor(1 + (len(sms_response) / 160))  # this is the number of texts sent

    # If SMS_LARGE_PENALTY, an sms response overflows 160 characters and becomes 2 messages, user is still charged

    rate_limited = False
    rate_limit_end = None
    if not rate_limit_service.is_admin(sender_no):
        sms_penalty = 1.0
        if config.SMS_LARGE_PENALTY:
            sms_penalty = float(num_texts)

        if rate_limit_service.is_rate_limited(sender_no, num_texts=sms_penalty):
            end_time = rate_limit_service.get_rate_limit_ending(sender_no, 1)
            str_end = end_time.strftime("%I:%M %p").lstrip('0')

            if config.RATE_LIMIT_WARNING_MESSAGE and not sender_no in rate_limit_service.rate_warned:
                rate_limit_service.rate_warned[sender_no] = True
                send_sms(sender_no, (dictionary.get_phrase("RATE_LIMITED") % str_end))

            rate_limited = True
            rate_limit_end = str_end
            return "Phone number is rate limited. Try again later."

        if config.RATE_LIMIT_WARNING_MESSAGE and sender_no in rate_limit_service.rate_warned:
            del rate_limit_service.rate_warned[sender_no]

    logger.info("SMS Response Generated - consumes %d SMS" % num_texts)

    print_task_info(body, num_texts, rate_limit_end, rate_limited, sender_no, sms_response, success)

    if wit_response is not None:
        logger.info(wit_response)
    send_sms(sender_no, sms_response)

    return sms_response


def parse_response(response):
    intent = response['outcomes'][0]['intent']
    if intent == 'getaroom':
        return parse_getaroom(response)
    elif intent == 'help':
        return True, dictionary.get_phrase("HELP")
    elif intent == 'stop':
        return parse_joke()
    else:
        return 'Invalid message. Try "get a room in TORG"'


def parse_getaroom(response):
    if 'outcomes' in response and len(response['outcomes']) > 0:
        outcome = response['outcomes'][0]
        if 'entities' in outcome and len(outcome['entities']) > 0:
            entities = outcome['entities']
            if 'building' in entities and len(entities['building']) > 0:

                # We'll parse out the building entities and select as many as possible with respect to the config
                buildings_to_parse = map(lambda x: x['value'], entities['building'])
                if len(buildings_to_parse) > config.MAX_BUILDINGS_IN_REQUEST:
                    buildings_to_parse = buildings_to_parse[:config.MAX_BUILDINGS_IN_REQUEST]

                current_time = datetime.now()

                if 'datetime' in entities and len(entities['datetime']) > 0:
                    time_str = entities['datetime'][0]['value']
                    current_time = dateutil.parser.parse(time_str)

                rooms = []
                for building_name in buildings_to_parse:
                    rooms += get_available_rooms(building_name, current_time, False)
                if len(rooms) == 0:
                    return False, dictionary.get_phrase("NO_ROOMS")

                else:
                    # Sort our collection of rooms
                    rooms.sort(key=operator.attrgetter('weight'), reverse=True)

                    # TODO: Add logic to determine room name here when multiple buildings are in solution set
                    building_name = rooms[0].building_name

                    string = ''
                    salutation = dictionary.get_phrase("INTRO")

                    # We'll say "hi" and that we found some rooms
                    if len(rooms) == 1:
                        phrase = "%s %s" % (salutation, dictionary.get_phrase("ONE_ROOM"))
                        string += phrase % (building_name,)
                    elif len(rooms) <= 3:
                        phrase = "%s %s" % (salutation, dictionary.get_phrase("SEVERAL_ROOMS"))
                        string += phrase % (len(rooms), building_name)
                    else:
                        phrase = "%s %s" % (salutation, dictionary.get_phrase("SEVERAL_MORE_ROOMS"))
                        string += phrase % (building_name,)

                iterations = min((config.NUM_ROOMS_TO_SHOW, len(rooms)))
                for i, room in enumerate(rooms[:iterations]):
                    if not room.end_availability:
                        string += '- %s %s (rest of day)' % (room.building_code, room.number)
                    else:
                        string += '- %s %s (until %s)' % (room.building_code, room.number, room.end_availability)
                    if i is not iterations - 1:
                        string += '\n'

                return True, string
    return False, dictionary.get_phrase("INVALID_MESSAGE")


def parse_joke():
    string = dictionary.get_phrase("PENGUIN_FACTS_WELCOME")
    fact = dictionary.get_phrase("PENGUIN_FACTS")
    string += fact
    return True, string


def send_sms(number, message, msg_type = "text"):
    if config.DEBUG_SMS:
        print("SMS DEBUG:\n%s\nfrom: %s\n===========" % (message, number))
        return

    msg = {
        'reqtype': 'json',
        'api_key': config.NEXMO_API_KEY,
        'api_secret': config.NEXMO_API_SECRET,
        'from': config.NEXMO_PHONE_NO,
        'to': number,
        'text': message,
        'type': msg_type
    }
    sms = NexmoMessage(msg)
    sms.set_text_info(msg['text'])
    response = sms.send_request()
    if not response:
        logger.error("[NEXMO] Failed to send response: %s [to] %s" % (message, number))
        print "Failed to send response"

    if config.LOG_MESSAGES:
        log_message(number, message, MessageDirection.OUTBOUND)


def send_to_wit(message):
    conn = httplib.HTTPSConnection('api.wit.ai')
    headers = {'Authorization': 'Bearer %s' % (config.WIT_ACCESS_TOKEN,)}
    params = urllib.urlencode({'v': '20141022', 'q': message})
    url = '/message?%s' % (params,)
    conn.request('GET', url, '', headers)
    response = conn.getresponse()
    return response.read()

def parse_unicode(message):
    return True, emoji.emojize("!! :face_throwing_a_kiss: !!")
    # return False, "Invalid message"