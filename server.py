# External dependencies
import wit
from flask import Flask
from nexmomessage import NexmoMessage # pip install -e git+https://github.com/marcuz/libpynexmo.git#egg=nexmomessage
from config import WIT_ACCESS_TOKEN

app = Flask(__name__)

@app.route('/getaroom')
def getaroom():
    # sender_no = request.args['msisdn']
    # body = request.args['text']

    # TODO: account for concatenated & unicode messages
    #
    # wit.init()
    # wit.text_query("get a room in torg", WIT_ACCESS_TOKEN, wit_callback)

    # must return 200 response!
    return 'Success!'
    

def wit_callback(response):
	print('Response: {}'.format(response))
	return 'lol'
	wit.close()
	
# msg = {
# 	'reqtype': 'json',
# 	'api_key': NEXMO_API_KEY,
# 	'api_secret': NEXMO_API_SECRET,
# 	'from': NEXMO_PHONE_NO,
# 	'to': sender_no,
# 	'text': 'Your message has been received.'
# }
# sms = NexmoMessage(msg)
# sms.set_text_info(msg['text'])
# sms.send_request()


if __name__ == "__main__":
    app.run()
