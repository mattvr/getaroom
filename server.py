import logging as logger

import rate_limit_service
import config
import message_logger as mlogger
import response_service

# External dependencies
from flask import Flask, request

app = Flask(__name__)

logger.basicConfig(filename=config.LOGGER_SERVER, level=logger.DEBUG)


@app.route('/getaroom', methods=['GET', 'POST'])
def getaroom():
    sender_no = request.values.get('msisdn')
    body = request.values.get('text')
    encoding = request.values.get('type')

    valid = True

    if sender_no is None or body is None:
        logger.error("RECEIVED INVALID MESSAGE.")
        valid = False
    else:
        if config.LOG_MESSAGES:
            mlogger.log_message(sender_no, body, mlogger.MessageDirection.INBOUND)

        if rate_limit_service.is_banned(sender_no):
            logger.warn("Number banned! - %s - %s", (body, sender_no))
            return "Number banned"


        logger.info("Received request - %s - %s" % (body, sender_no))

    if not valid:
        return "Invalid message"

    return response_service.parse_sms_main(body, sender_no, encoding)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
