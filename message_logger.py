import sqlite3
import config
from utils import enum

MessageDirection = enum('INBOUND', 'OUTBOUND')

get_client_from_number_query = "SELECT * FROM clients WHERE phone_number = ?;"

# 0 = incoming
# 1 = outgoing
def log_message(phone_number, body, direction):
    con = sqlite3.connect(config.SQLITE_DATABASE)
    cur = con.cursor()

    cur.execute(get_client_from_number_query, (phone_number,))
    client = cur.fetchone()

    if client is None:
        q = "INSERT INTO clients VALUES (NULL, ?);"
        cur.execute(q, (phone_number,))
        client_id = cur.lastrowid
    else:
        client_id = client[0]

    q = "INSERT INTO messages VALUES (NULL, ?, ?, ?, CURRENT_TIMESTAMP);"
    cur.execute(q, (client_id, direction, body,))

    con.commit()
    cur.close()
    cur.close()

def get_count(phone_number):
    con = sqlite3.connect(config.SQLITE_DATABASE)
    cur = con.cursor()

    result = 0

    cur.execute(get_client_from_number_query, (phone_number, ))
    client = cur.fetchone()
    if client is not None:
        client_id = client[0]
        q = "SELECT count(*) FROM messages WHERE client_id = ?;"
        cur.execute(q, (client_id, ))
        num = cur.fetchone()
        result = num[0]

    cur.close()
    con.close()

    return result