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
    "Sunday"    : "S",
    "Monday"    : "M",
    "Tuesday"   : "T",
    "Wednesday" : "W",
    "Thursday"  : "R",
    "Friday"    : "F",
    "Saturday"  : "X"
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
            continue
        building = rows[0]

        # Now let's get all the rooms from the building
        cur.execute("SELECT * FROM rooms WHERE building_id = '" + str(building[0]) + "';")
        rooms = cur.fetchall()
        if len(rooms) == 0:
            print "No rooms found in that building. How strange."
            return
        print "Found %i rooms!" % len(rooms)

        valid_rooms = []
        for db_room in rooms:
            cur.execute("SELECT * FROM times WHERE room_id = '"+ str(db_room[0]) +"';")
            times = cur.fetchall()

            is_valid = True
            next_unavailable = None

            for class_time in times:
                class_days = json.loads(class_time[5])
                current_day = day_translation[time.strftime("%A")]

                # Only look at classes occuring today
                if current_day not in class_days:
                    continue

                time_start = time.strptime(class_time[3], TIME_OUT_FORMAT)
                time_end = time.strptime(class_time[4], TIME_OUT_FORMAT)

                if time_contained(time_start, time_end, datetime.now()):
                    is_valid = False
                    break

                # Next class should represent when room is occupied

                # Next_unavailable is unset, and class_time > this time
                if next_unavailable is None and time_greater(time_start.tm_hour, time_start.tm_min, datetime.now().hour, datetime.now().minute):
                    next_unavailable = time_start
                # Class_time < next_unavailable
                elif next_unavailable is not None and time_greater(time_start.tm_hour, time_start.tm_min, datetime.now().hour, datetime.now().minute) and time_lesser(time_start.tm_hour, time_start.tm_min, next_unavailable.tm_hour, next_unavailable.tm_min):
                    next_unavailable = time_start

            if is_valid:
                valid_rooms.append((db_room, next_unavailable))

        if len(valid_rooms) == 0:
            print "Sorry, there are no rooms available in this building right now. :("
        else:
            # TODO: print next class time for this room
            print "Got %i available rooms:" % len(valid_rooms)
            for room, room_time in valid_rooms:
                if room_time is not None:
                    time_as_str = time.strftime(TIME_IN_FORMAT, room_time)
                    print "%s %s is available until %s" % (building[1], room[1], time_as_str)
                else:
                    print "%s %s is available for the rest of the day." % (building[1], room[1])
        cur.close()
    return

# This is ugly, I know.
def time_contained(start, end, time):
    # if time.hour >= start.tm_hour and time.hour <= end.tm_hour:
    if start.tm_hour <= time.hour <= end.tm_hour:
        # Same hour as start time
        if (time.hour == start.tm_hour and time.minute >= start.tm_min and
                (time.hour != end.tm_hour or time.minute <= end.tm_min)):
            return True
        # Later hour than start time
        elif (time.hour > start.tm_hour and ((time.hour == end.tm_hour and
                                              time.minute < end.tm_min) or (time.hour < end.tm_hour))):
            return True
    return False

def time_greater(time1hour, time1min, time2hour, time2min):
    return time1hour > time2hour or (time1hour == time2hour and time1min > time2min)

def time_lesser(time1hour, time1min, time2hour, time2min):
    return time1hour < time2hour or (time1hour == time2hour and time1min < time2min)

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
            cur.execute("SELECT * FROM buildings WHERE code = ?;", building)
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
