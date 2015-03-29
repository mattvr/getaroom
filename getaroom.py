from bs4 import BeautifulSoup
from time import gmtime, strftime
import datetime
import time
import collections
import sys
import re
import sqlite3
import json

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

# eg. 1:25PM
IN_TIME_FORMAT = "%i:%M%p"



# Supports:
#   help
#   in
#	import
#	export
#	populate
def main(argv):
    directive = "help"

    options = {"help"     : pub_help,
               "in"       : pub_get_room_in,
               "import"   : pub_import_json,
               "export"   : pub_export_json,
               "populate" : pub_populate}

    if options.has_key(argv[0]):
        directive = argv[0]
    options[directive](argv[1:])


def pub_help(args):
    print("Usage: ")
    return
def pub_get_room_in(args):
    print("Getting a room in "+ args[0])
    return
def pub_import_json(args):
    return
def pub_export_json(args):
    return
def pub_populate(args):
    if len(args) == 0:
        source_file = 'timetable.html'
    else:
        source_file = args[0]

    populate(source_file)
    return

def populate(source_file):
    # file = open(database, 'w')
    con = sqlite3.connect('data.db')

    print "Loading %s..." % source_file,
    soup = BeautifulSoup(open(source_file, 'r'))
    print '\033[92m'+"done"+'\033[0m'

    rows = soup.table.tbody.find_all('tr')
    rows = rows[1:]  # ignore title row

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
            cur.execute("SELECT * FROM buildings WHERE code = '"+building+"';")
            rows = cur.fetchall()
            if len(rows) == 0:
                cur.execute("INSERT INTO buildings VALUES(null, '"+building+"', null);")
                building_id = cur.lastrowid
            else:
                building_id = rows[0][0]

            # Insert rooms
            cur.execute("SELECT * FROM rooms WHERE building_id = '"+str(building_id)+"' AND name = '"+room+"';")
            rows = cur.fetchall()
            if len(rows) == 0:
                cur.execute("INSERT INTO rooms VALUES(null, '"+room+"', "+str(building_id)+");")
                room_id = cur.lastrowid
            else:
                room_id = rows[0][0]

            days = days.replace(" ", "")
            days_list = list(days)
            days_string = json.dumps(days_list)
            cur.execute("INSERT INTO times VALUES(null, '"+str(room_id)+"', '"+start_time+"', '"+end_time+"', '"+days_string+"');")



            # # print "Parsing session: %s %s : %s %s-%s" % (building, room, days, start_time, end_time)
            #
            # # Add buildings
            # db_buildings = backend.filter(Building, {'id': building})
            # if len(db_buildings) == 0:
            #     db_building = Building({'id': building, 'rooms': []})
            #     db_building.save(backend)
            #     # print("Created building")
            # else:
            #     db_building = db_buildings[0]
            #     # print("Building exists")
            #
            # # Add rooms to buildings
            # room_data = {'id': room, 'schedule': schedule}
            # print(room_data)
            # if room_data not in db_building.rooms:
            #     db_building.rooms.append(room_data)
            # print(db_building)
            # db_building.save(backend)
            #
            # # Add times to schedule
            # days_array = days.split(' ')
            # time = {'days': days_array, 'start': start_time, 'end': end_time}
            #
            #
            # backend.commit()
    con.close()



def get_available_rooms(building, time):
    avail = []
    for room in building:
        if room.is_available(time):
            avail.append(room)

    if len(avail) > 0:
        print 'There are %d available rooms in your building.' % len(avail)
        for room in avail:
            print room.id
        # print room.days
    else:
        # Idea: Log most commonly requested buildings following this request. Offer room in that
        # building instead.
        print 'There are no available rooms in your building. :('

#
# class Classroom(object):
#     def is_available(self, time):
#         return True
#
#     def __eq__(self, other):
#         return self.number == other.number
#
#     # def when_available():



if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1:])
    else:
        pub_help(0)
