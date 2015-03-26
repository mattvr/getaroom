from bs4 import BeautifulSoup
from time import gmtime, strftime
import datetime
import collections

soup = BeautifulSoup(open('timetable.html', 'r'))

rows = soup.table.tbody.find_all('tr')
rows = rows[1:] # ignore title row

buildings = { } # Name, List of Classes

def populate():
    for i, row in enumerate(rows):
        loc_string = row.find_all('td')[-2].get_text().encode('ascii','ignore')

        # Ignore TBA rooms
        if (loc_string == 'TBA'):
            continue

        loc_split = loc_string.split(' ', 1)
        building = loc_split[0]

        number = ''
        if len(loc_split) > 1:
            number = loc_split[1]

        # Add new building
        if building not in buildings:
            buildings[building] = []

        # Add new rooms
        if number not in buildings[building]:
            buildings[building].append(number);

populate()

print(buildings['MCB'])


# class Classroom(object):
# 	def __init__(self):
# 		self.building = "" # e.g. TORG
# 		self.schedule = [] # M T W R F

# 	def is_available(time):
# 		return True

# 	def when_available():


# 	def when_unavailable():

# class Schedule(object):

# class Datetime(object):
# 	def __init__(self):

