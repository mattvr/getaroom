# Dillinger
##VT Open Classroom Search
---
###What is this?
getaroom is a python script that assists clients in finding rooms on the Virginia Tech campus that not consumed by classes. The purpose of this is to allow classrooms to be better utilized during off-hours as well as help students find the best possible study location where they will not be disturbed or be disturbing anyone else.
### How does it work?
We have collected a log of all classes in the Spring 2015 semester and parsed them into a SQLite database. This database is queried and determined if a room is available in a specified building. This interface is linked with Nexmo, an SMS api. Nexmo sends SMS data to a small http server that runs constantly (server.py). When a message is received by the endpoint, it is passed to wit.ai for machine learning-assisted intent determination. Once the intent is determined, we send a response SMS with the expected data.

### Installation
TODO