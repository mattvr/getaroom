import json
import httplib, urllib

# External dependencies
import wit
import Queue
from flask import Flask, request
from nexmomessage import NexmoMessage # pip install -e git+https://github.com/marcuz/libpynexmo.git#egg=nexmomessage
from config import WIT_ACCESS_TOKEN, NEXMO_API_KEY, NEXMO_API_SECRET, NEXMO_PHONE_NO

app = Flask(__name__)

@app.route('/getaroom')
def getaroom():
    sender_no = request.args.get('msisdn', '')
    body = request.args.get('text', '')

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
                return "Looking for room in %s" % (building)
    return "Invalid message. Try 'get a room in TORG'"

def send_sms(number, message):
    msg = {
        'reqtype': 'json',
        'api_key': NEXMO_API_KEY,
        'api_secret': NEXMO_API_SECRET,
        'from': NEXMO_PHONE_NO,
        'to': number,
        'text': message
    }
    sms = NexmoMessage(msg)
    sms.set_text_info(msg['text'])
    sms.send_request()

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
