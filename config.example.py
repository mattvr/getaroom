NEXMO_API_KEY    = ''
NEXMO_API_SECRET = ''
NEXMO_PHONE_NO   = ''

WIT_ACCESS_TOKEN = ''

SQLITE_DATABASE      = 'data/data.db'
BUIlDING_NAME_LOOKUP = 'data/buildings.json'

# Log files
LOGGER_SERVER  = 'logs/server.log'
LOGGER_SERVICE = 'logs/getaroom.log'

# These numbers will be blocked
BLACKLIST = 'config/blacklist.json'

# Print texts to console instead of sending SMS
DEBUG_SMS = True

# 10 texts a day
SMS_PER_PERIOD = 10
SMS_PERIOD     = 86400

# Count if a generic text consumes more than one message (long building name)
SMS_LARGE_PENALTY = False

DICTIONARY_FILE = "config/dictionary.json"
DEFAULT_LANGUAGE = "en"

# Maintain a log of all inbound and outbound messages in the database
# Also logs phone numbers
LOG_MESSAGES = True