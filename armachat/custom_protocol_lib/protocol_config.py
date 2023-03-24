AES_KEY = "SuperTajne heslo" #TODO web configurable => move to json

MY_ADDRESS = 0x0001 #TODO web configurable => move to json, but can be configured only once
CONTACT = 0x0005

RESEND_COUNT = 3 #TODO web configurable => move to json
RESEND_TIMEOUT = 5 #Seconds #TODO web configurable => move to json
ACK_WAIT_TIME = 60 #Seconds #TODO web configurable => move to json
DELETE_WAIT_TIME = 120 #Seconds

DEFAULT_MAX_HOP = 5 #TODO web configurable => move to json
DEFAULT_TTL = 50 #Seconds (max 2B - 65536) #TODO web configurable => move to json
RANDOMIZE_PATH = False #TODO web configurable => move to json

MONITORING = False

# Do not change this values
#TODO move non-configurable values to class definitions
BROADCAST_ADDRESS = 0xFFFF
HEADER_LENGTH = 12
