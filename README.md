#VT Open Classroom Search

##What is this?
`getaroom` helps you find empty classrooms on Virginia Tech's campus.

##Why?
This helps students find quiet places to study on campus and enables better utilization of space at the university.

## How does it work?
####Components:
1. SQLite database of all class times Spring 2015 @ VT
2. Simple Flask python server, which serves HTTP requests
3. Nexmo, a cheap phone number & text message service
4. Wit.ai, a natural language processing tool

####Process:
1. The Flask server is constantly running
2. A user texts our phone number, Nexmo routes this request to our server's URL via HTTP GET or POST
3. Our server passes the user's message to Wit.ai, where meaning is extracted.
4. If a valid building is sent, we query our class database to check available rooms
5. We respond with the available rooms!

## Installation
TODO