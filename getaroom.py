from bs4 import BeautifulSoup
from time import gmtime, strftime
import datetime
import time
import collections
import sys
import re
from blitzdb import Document
from blitzdb import FileBackend

# Example match:
# M W F
# 12:20PM
# 1:10PM
# # LITRV 1670
pattern = "(?P<days>(?:(?:M|T|W|R|F)\s?)+)\s*(?P<start_time>\d\d?:\d\d(?:AM|PM))\s*(?P<end_time>\d\d?:\d\d(?:AM|PM))\s*(?:(?P<building>(?:\w)+)) (?P<room>(?:\w| )*)"


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

# database
backend = FileBackend("data")

# Database Docs
class Building(Document):
    pass
class Room:
    def __init__(self):
        self.data = []
class Schedule:
    def __init__(self):
        self.data = []
class Time:
    def __init__(self):
        self.data = []

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


        # print "Parsing session: %s %s : %s %s-%s" % (building, room, days, start_time, end_time)


        # Add buildings
        db_buildings = backend.filter(Building, {'id': building})
        if len(db_buildings) == 0:
            db_building = Building({'id': building, 'rooms': []})
            db_building.save(backend)
            # print("Created building")
        else:
            db_building = db_buildings[0]
            # print("Building exists")

        # Add rooms to buildings
        if room not in db_building.rooms:
            db_building.rooms.append(room)
        print(db_building)
        db_building.save(backend)
        backend.commit()
        #
        # time = Time({'start': start_time, 'end': end_time, 'days': days})
        # schedule = Schedule({'period': 'Fall 2015', 'time': time}) # WONT need to merge
        #
        #
        # if db_building is None:
        #
        # else:
        #     db_rooms = db_building.rooms
        #
        #     if db_rooms is None:
        #         db_rooms = [Room({'id': room})]
        #
        #     db_room = db_rooms.get(Room, {'id': room})
        #
        #     if db_room is None:
        #         db_room = Room({'id': room})
        #
        #     db_building.rooms.append(room)
        #
        # db_building.save(backend)


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


buildings = {}  # Name, List of Classes