import json
from datetime import datetime
import httplib, urllib

# External dependencies
import Queue
from flask import Flask, request
from nexmomessage import NexmoMessage # pip install -e git+https://github.com/marcuz/libpynexmo.git#egg=nexmomessage

from config import WIT_ACCESS_TOKEN, NEXMO_API_KEY, NEXMO_API_SECRET, NEXMO_PHONE_NO
from getaroom import get_available_rooms, ClassRoom

app = Flask(__name__)

@app.route('/getaroom', methods=['GET', 'POST'])
def getaroom():
    sender_no = request.values.get('msisdn')
    body = request.values.get('text')

    if sender_no is None or body is None:
        return 'Invalid message.'

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
                    best_room = rooms[0]
                    if not best_room.end_availability:
                        return "%s %s is available for the rest of the day" % (best_room.building_code, best_room.number)
                    else:
                        return "%s %s is available until %s" % (best_room.building_code, best_room.number, best_room.end_availability)

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
