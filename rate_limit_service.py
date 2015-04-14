from datetime import datetime, timedelta
import time
import logging as logger
import sqlite3
import json

from config import SMS_PER_PERIOD, SMS_PERIOD, SQLITE_DATABASE, BLACKLIST


DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

rate_warned = {}

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

def get_rate_limit_ending(phone_num, allowance = 1):
    con = sqlite3.connect(SQLITE_DATABASE)
    cur = con.cursor()
    q = "SELECT * FROM rate_limit_logs WHERE phone_number = ?"
    cur.execute(q, (phone_num, ))

    result = cur.fetchone()
    if result is None:
        return 0
    time_left = allowance - result[3]
    if time_left > allowance:
        return 0

    time_left *= (SMS_PERIOD / SMS_PER_PERIOD)
    m, s = divmod(time_left, 60)
    h, m = divmod(m, 60)

    dt_end_limit = datetime.now() + timedelta(hours=h, minutes=m, seconds=s)

    return dt_end_limit



def get_time_remaining(phone_num, allowance = 1):
    end_time = get_rate_limit_ending(phone_num, allowance)
    time_remaining = end_time - datetime.now()
    s = time_remaining.seconds

    hours = s // 3600
    s -= hours * 3600
    minutes = s // 60
    seconds = s - (minutes * 60)
    print '%s:%s:%s' % (hours, minutes, seconds)

def is_banned(number):
    ban_lookup = json.loads(open(BLACKLIST).read())
    bans = ban_lookup['bans']
    if number in bans:
        return True
    return False