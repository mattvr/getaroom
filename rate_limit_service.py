from datetime import datetime
import time
import logging as logger
import sqlite3

from config import SMS_PER_PERIOD, SMS_PERIOD, SQLITE_DATABASE

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

def update_rate(phone_number):
    con = sqlite3.connect(SQLITE_DATABASE)
    cur = con.cursor()

    q = "SELECT * FROM rate_limit_logs WHERE phone_number = ?"
    cur.execute(q, (phone_number,))

    rate = cur.fetchone()
    # current_time = datetime.strftime(DATETIME_FORMAT)
    current_time = time.strftime(DATETIME_FORMAT)
    if rate is None:
        logger.info("Creating new rate limiting entry for %s" % phone_number)
        q = "INSERT INTO rate_limit_logs VALUES (NULL, ?, ?, NULL, ?);"
        cur.execute(q, (phone_number, current_time, 0))
    else:
        datet1 = datetime.strptime(rate[2], DATETIME_FORMAT)

        datet2 = datetime.strptime(rate[3], DATETIME_FORMAT)

        new_count = rate[4] + 1
        new_time = current_time
        if (datet1 - datet2).seconds > SMS_PERIOD:
            new_count = 0

        q = "UPDATE rate_limit_logs SET count = ?, last_time = ? WHERE phone_number = ?"
        cur.execute(q, (new_count, current_time, phone_number))
    cur.close()


def is_rate_limited(phone_number):
    con = sqlite3.connect(SQLITE_DATABASE)
    cur = con.cursor()

    q = "SELECT * FROM rate_limit_logs WHERE phone_number = ?"
    cur.execute(q, (phone_number,))

    rate = cur.fetchone()

    if rate is None:
        return False

    t1 = rate[2]
    t2 = rate[3]
    count = rate[4]

    retval = False
    if not t2:
        retval = False
    elif count > SMS_PER_PERIOD:
        retval = True

    # datet1 = datetime.strptime(t1, DATETIME_FORMAT)
    # datet2 = datetime.strptime(t2, DATETIME_FORMAT)
    # if (datet1 - datet2).seconds > SMS_PERIOD

    cur.close()
    return retval