import logging as logger

from rate_limit_service import is_banned
from config import LOGGER_SERVER, LOG_MESSAGES
from message_logger import log_message, MessageDirection
from response_service import parse_sms_main

# External dependencies
from flask import Flask, request

app = Flask(__name__)

logger.basicConfig(filename=LOGGER_SERVER, level=logger.DEBUG)


@app.route('/getaroom', methods=['GET', 'POST'])
def getaroom():
    sender_no = request.values.get('msisdn')
    body = request.values.get('text')
    type = request.values.get('type')

    allowed_types = ['text']

    if sender_no is None or body is None or (type is not None and type not in allowed_types ):
        logger.error("RECEIVED INVALID MESSAGE.")
        return 'Invalid message.'

    if LOG_MESSAGES:
        log_message(sender_no, body, MessageDirection.INBOUND)

    if is_banned(sender_no):
        logger.warn("Number banned! - %s - %s", (body, sender_no))
        return "Number banned"

    logger.info("Received request - %s - %s" % (body, sender_no))

    return parse_sms_main(body, sender_no)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
