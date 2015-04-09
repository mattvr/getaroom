from datetime import datetime
import time
import logging as logger
import sqlite3
import json

from config import SMS_PER_PERIOD, SMS_PERIOD, SQLITE_DATABASE, BLACKLIST


DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'


def is_rate_limited(phone_number, num_texts=1.0):
    con = sqlite3.connect(SQLITE_DATABASE)
    cur = con.cursor()

    rate = SMS_PER_PERIOD
    allowance = rate

    current_time = time.strftime(DATETIME_FORMAT)

    q = "SELECT * FROM rate_limit_logs WHERE phone_number = ?"
    cur.execute(q, (phone_number,))

    rate_log = cur.fetchone()

    if rate_log is None:
        logger.info("Creating new rate limiting entry for %s" % phone_number)
        q = "INSERT INTO rate_limit_logs VALUES (NULL, ?, ?, ?);"
        cur.execute(q, (phone_number, current_time, allowance - 1))
        con.commit()
        cur.close()
        con.close()
        return False

    last_check = datetime.strptime(rate_log[2], DATETIME_FORMAT)
    time_passed = datetime.strptime(current_time, DATETIME_FORMAT) - last_check

    ratio = float(SMS_PER_PERIOD) / float(SMS_PERIOD)
    allowance = rate_log[3] + time_passed.seconds * ratio

    q = "UPDATE rate_limit_logs SET last_time = ?, allowance = ? WHERE id = ?"
    cur.execute(q, (current_time, allowance, rate_log[0]))

    if allowance > rate:
        allowance = rate
        q = "UPDATE rate_limit_logs SET allowance = ? WHERE id = ?"
        cur.execute(q, (allowance, rate_log[0]))
    if allowance < 1.0:
        ret_val = True
    else:
        ret_val = False
        allowance -= num_texts
        q = "UPDATE rate_limit_logs SET allowance = ? WHERE id = ?"
        cur.execute(q, (allowance, rate_log[0]))
    con.commit()
    cur.close()
    con.close()
    return ret_val


def is_banned(number):
    ban_lookup = json.loads(open(BLACKLIST).read())
    bans = ban_lookup['bans']
    if number in bans:
        return True
    return False