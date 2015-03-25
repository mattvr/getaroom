from bs4 import BeautifulSoup
from time import gmtime, strftime

soup = BeautifulSoup(open("timetable.html", 'r'))

print(soup.prettify())

# class Classroom(object):
# 	def __init__(self):
# 		self.building = "" # e.g. TORG
# 		self.schedule = [] # M T W R F

# class Schedule(object):

# class Datetime(object):
# 	def __init__(self):

