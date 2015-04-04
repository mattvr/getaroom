import sqlite3
from config import SQLITE_DATABASE
from utils import enum

MessageDirection = enum('INBOUND', 'OUTBOUND')

# 0 = incoming
# 1 = outgoing
def log_message(phone_number, body, direction):
    con = sqlite3.connect(SQLITE_DATABASE)
    cur = con.cursor()

    q = "SELECT * FROM clients WHERE phone_number = ?;"
    cur.execute(q, (phone_number,))
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
    pass