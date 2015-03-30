from datetime import datetime
import time
import sys
import re
import sqlite3
import json

from bs4 import BeautifulSoup


# Example match:
# M W F
# 12:20PM
# 1:10PM
# # LITRV 1670
pattern = "(?P<days>(?:(?:M|T|W|R|F)\s?)+)\s*(?P<start_time>\d\d?:\d\d(?:AM|PM))\s*(?P<end_time>\d\d?:\d\d(?:AM|PM))\s*(?:(?P<building>(?:\w)+)) (?P<room>(?:\w| )*)"
database = "timetable.db"

regex = re.compile(pattern)

day_lookup = {
    "M": 0,
    "T": 1,
    "W": 2,
    "R": 3,
    "F": 4
}

day_translation = {
    "Sunday": "S",
    "Monday": "M",
    "Tuesday": "T",
    "Wednesday": "W",
    "Thursday": "R",
    "Friday": "F",
    "Saturday": "X"
}

# eg. 1:25PM
TIME_IN_FORMAT = "%I:%M%p"
TIME_OUT_FORMAT = "%H:%M"


class ClassRoom:
    def __init__(self):
        pass


# Supports:
# help
#   in
#	populate
def main(argv):
    directive = "help"

    options = {"help": pub_help,
               "in": pub_get_room_in,
               # "import"   : pub_import_json,
               # "export"   : pub_export_json,
               "populate": pub_populate}

    if options.has_key(argv[0]):
        directive = argv[0]
    options[directive](argv[1:])


def pub_help(args):
    print("Usage: ")
    return


def pub_get_room_in(args):
    while 1:
        building_string = raw_input("Enter a building: ")
        print("Getting a room in " + building_string + "...")
        con = sqlite3.connect('data.db')

        # building_string = args[0]
        # First ensure we have that building
        cur = con.cursor()
        cur.execute("SELECT * FROM buildings WHERE code = '" + building_string + "';")
        rows = cur.fetchall()
        if len(rows) == 0:
            print "Sorry, we don't have that building in our database! Try another."
            return
        building = rows[0]

        # Now let's get all the rooms from the building
        cur.execute("SELECT * FROM rooms WHERE building_id = '" + str(building[0]) + "';")
        rooms = cur.fetchall()
        if len(rooms) == 0:
            print "No rooms found in that building. How strange."
            return
        print "Found %i rooms!" % len(rooms)

        # Get all the times from the building
        cur.execute("SELECT * FROM times WHERE building_id = '" + str(building[0]) + "';")
        times = cur.fetchall()
        print "Found %i classes in this building" % len(times)

        current_time = datetime.now()

        passing_times = []
        passing_rooms = []

        for class_time in times:
            # print(class_time[3])
            time_start_struct = time.strptime(class_time[3], TIME_OUT_FORMAT)
            time_end_struct = time.strptime(class_time[4], TIME_OUT_FORMAT)

            passing_start = False
            passing_end = False
            passing_day = False

            # Check days
            current_day = day_translation[time.strftime("%A")]
            days = json.loads(class_time[5])
            if current_day not in days:
                passing_day = True

            if passing_day:
                passing_times.append(class_time)
                continue

            # Check hours and minutes
            if current_time.time().hour < time_start_struct.tm_hour:
                passing_start = True
            elif current_time.time().hour == time_start_struct.tm_hour:
                if current_time.time().minute < time_start_struct.tm_min:
                    passing_start = True

            if current_time.time().hour > time_end_struct.tm_hour:
                passing_end = True
            elif current_time.time().hour == time_start_struct.tm_hour:
                if current_time.time().minute > time_end_struct.tm_min:
                    passing_start = True

            if passing_end or passing_start:
                passing_times.append(class_time)

        if len(passing_times) == 0:
            print "Sorry, there are no rooms available in this building right now. :("
        else:
            for p in passing_times:
                if not p[1] in passing_rooms:
                    passing_rooms.append(p[1])
            print "Got %i available rooms:" % len(passing_rooms)
            for r in passing_rooms:
                cur.execute("SELECT * FROM rooms WHERE id = '" + str(r) + "';")
                room = cur.fetchone()
                print room[1]
        cur.close()
    return


def pub_populate(args):
    if len(args) == 0:
        source_file = 'timetable.html'
    else:
        source_file = args[0]

    populate(source_file)
    return


# Writes a SQLite database from source_file html table
def populate(source_file):
    con = sqlite3.connect('data.db')

    print "Loading %s..." % source_file,
    soup = BeautifulSoup(open(source_file, 'r'))
    print '\033[92m' + "done" + '\033[0m'

    rows = soup.table.tbody.find_all('tr')
    rows = rows[1:]  # ignore title row

    print "Writing database..."
    for i, row in enumerate(rows):
        text = row.get_text().encode('ascii', 'ignore')

        # See if pattern matches
        # result = re.search(regex, text)

        result = regex.search(text)
        if result is None:
            continue

        # Get capture groups
        days = result.group("days")
        building = result.group("building")
        room = result.group("room")
        start_time = result.group("start_time")
        end_time = result.group("end_time")

        # print(json.dumps(days))

        with con:
            cur = con.cursor()

            # Insert buildings
            cur.execute("SELECT * FROM buildings WHERE code = '" + building + "';")
            rows = cur.fetchall()
            if len(rows) == 0:
                cur.execute("INSERT INTO buildings VALUES(NULL, '" + building + "', NULL);")
                building_id = cur.lastrowid
            else:
                building_id = rows[0][0]

            # Insert rooms
            cur.execute("SELECT * FROM rooms WHERE building_id = '" + str(building_id) + "' AND name = '" + room + "';")
            rows = cur.fetchall()
            if len(rows) == 0:
                cur.execute("INSERT INTO rooms VALUES(NULL, '" + room + "', " + str(building_id) + ");")
                room_id = cur.lastrowid
            else:
                room_id = rows[0][0]

            days = days.replace(" ", "")
            days_list = list(days)
            days_string = json.dumps(days_list)

            time_start_struct = time.strptime(start_time, TIME_IN_FORMAT)
            time_end_struct = time.strptime(end_time, TIME_IN_FORMAT)

            time_start_db = time.strftime(TIME_OUT_FORMAT, time_start_struct)
            time_end_db = time.strftime(TIME_OUT_FORMAT, time_end_struct)

            cur.execute("INSERT INTO times VALUES(NULL, '" + str(room_id) + "', '" + str(
                building_id) + "', '" + time_start_db + "', '" + time_end_db + "', '" + days_string + "');")
    con.close()


def get_available_rooms(building, time):
    pass

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1:])
    else:
        pub_help(0)
