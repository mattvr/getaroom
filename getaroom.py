from bs4 import BeautifulSoup
from time import gmtime, strftime
import datetime
import time
import collections
import sys
import getopt

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
# help
# in
#	import
#	export
#	populate
def main(argv):
    directive = "help"
    try:
        opts, args = getopt.getopt(argv, "hb:i:x:p:", ["help",
                                                       "building=",
                                                       "import=",
                                                       "export=",
                                                       "populate="])
    except getopt.GetoptError:
        print("Improper invocation")
        sys.exit(2);


def populate():
    for i, row in enumerate(rows):
        cells = row.find_all('td')

        # Get the classroom
        first = cells[-1].get_text().encode('ascii', 'ignore')
        loc_str = cells[-2].get_text().encode('ascii', 'ignore')
        start_str = cells[-4].get_text().encode('ascii', 'ignore')
        end_str = cells[-3].get_text().encode('ascii', 'ignore')

        # Ignore TBA rooms
        if (loc_str == 'TBA' or start_str == '(ARR)' or first == 'Staff'):
            continue

        loc_split = loc_str.split(' ', 1)
        building = loc_split[0]

        number = ''
        if len(loc_split) > 1:
            number = loc_split[1]

        # Add new building
        if building not in buildings:
            buildings[building] = []

        room = Classroom()
        room.number = number

        # Add new rooms
        if room not in buildings[building]:
            new_room = Classroom()
            new_room.number = number
            buildings[building].append(new_room)

        # Parse days & times
        start_str = cells[-4].get_text().encode('ascii', 'ignore')

        # time_start = time.strptime(start_str, IN_TIME_FORMAT)
        # time_end   = time.strptime(end_str, IN_TIME_FORMAT)

        days_str = cells[-5].get_text().encode('ascii', 'ignore')

        print days_str

        # Convert M -> 0, T -> 1, etc.
        days_split = days_str.split(' ')
        days_converted = []
    # for day in days_split:
    # 	print day
    # days_converted.append(day_lookup[day])
    # buildings[building].days = days_converted


def get_available_rooms(building, time):
    avail = []
    for room in building:
        if room.is_available(time):
            avail.append(room)

    if len(avail) > 0:
        print 'There are %d available rooms in your building.' % len(avail)
        for room in avail:
            print room.number
        # print room.days
    else:
        # Idea: Log most commonly requested buildings following this request. Offer room in that
        # building instead.
        print 'There are no available rooms in your building. :('


class Classroom(object):
    def is_available(self, time):
        return True

    def __eq__(self, other):
        return self.number == other.number

    # def when_available():


soup = BeautifulSoup(open('timetable.html', 'r'))

rows = soup.table.tbody.find_all('tr')
rows = rows[1:]  # ignore title row

buildings = {}  # Name, List of Classes

# populate()

if __name__ == "__main__":
    main(sys.argv[1:])

get_available_rooms(buildings['MCB'], 1500)