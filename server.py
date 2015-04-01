import json
from datetime import datetime
import httplib, urllib
import logging as logger

# External dependencies
import Queue
from flask import Flask, request
from nexmomessage import NexmoMessage # pip install -e git+https://github.com/marcuz/libpynexmo.git#egg=nexmomessage

from config import WIT_ACCESS_TOKEN, NEXMO_API_KEY, NEXMO_API_SECRET, NEXMO_PHONE_NO, LOGGER_SERVER
from getaroom import get_available_rooms, ClassRoom

app = Flask(__name__)

logger.basicConfig(filename=LOGGER_SERVER,level=logger.DEBUG)
@app.route('/getaroom', methods=['GET', 'POST'])
def getaroom():
    sender_no = request.values.get('msisdn')
    body = request.values.get('text')

    if sender_no is None or body is None:
        return 'Invalid message.'

    logger.info("Received request - %s - %s" % (body, sender_no))

    # TODO: account for concatenated & unicode messages
    wit_response = send_to_wit(body)
    sms_response = parse_response(json.loads(wit_response))
    send_sms(sender_no, sms_response)
    print wit_response

    return sms_response

def send_to_wit(message):
    conn = httplib.HTTPSConnection('api.wit.ai')
    headers = {'Authorization': 'Bearer %s' % (WIT_ACCESS_TOKEN)}
    params = urllib.urlencode({'v': '20141022', 'q': message})
    url = '/message?%s' % (params)
    conn.request('GET', url, '', headers)
    response = conn.getresponse()
    return response.read()

def parse_response(response):
    if 'outcomes' in response and len(response['outcomes']) > 0:
        outcome = response['outcomes'][0]
        if 'entities' in outcome and len(outcome['entities']) > 0:
            entity = outcome['entities']
            if 'building' in entity and len(entity['building']) > 0:
                building = entity['building'][0]['value']

                rooms = get_available_rooms(building, datetime.now())
                if len(rooms) == 0:
                    return "Sorry, there aren't any rooms available in that building right now."
                else:
                    string = ''
                    if len(rooms) == 1:
                        string += 'Hey! I found one room in %s:\n' % (building)
                    elif len(rooms) <= 2:
                        string += 'Hey! I found %d rooms in %s:\n' % (len(rooms), building)
                    else:
                        string += 'Hey! Here are the three best rooms in %s:\n' % (building)

                iterations = min((3, len(rooms)))
                for i, room in enumerate(rooms[:iterations]):
                    if not room.end_availability:
                        string += '- %s %s is available for the rest of the day' % (room.building_code, room.number)
                    else:
                        string += '- %s %s is available until %s' % (room.building_code, room.number, room.end_availability)
                    if i is not iterations - 1:
                        string += '\n'
                return string

    return "Invalid message. Try 'get a room in TORG'"

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
        print "Failed to send response"

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
