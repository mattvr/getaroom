from datetime import datetime
import logging as logger
import sqlite3

from config import SMS_PER_PERIOD, SMS_PERIOD, SQLITE_DATABASE


def update_rate(phone_number):
    pass

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

    if not t2:
        return False