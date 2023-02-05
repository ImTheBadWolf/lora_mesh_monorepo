from enum import Enum
import random
from binascii import hexlify
import config
#import aesio

def calculate_checksum(data):
  #Calculates CRC-16/CCITT-FALSE checksum of first 8 bytes of data
  crc = 0xFFFF
  polynomial = 0x1021
  for byte in data[0:8]:
    crc ^= byte << 8
    for bit in range(0, 8):
      if crc & 0x8000:
        crc = (crc << 1) ^ polynomial
      else:
        crc <<= 1
  return crc & 0xFFFF

def fill_spaces(string, length):
  if len(string) % 2 != length % 2:
    string += " "
  return " " * int((length - len(string))/2) + string + " " * int((length - len(string))/2)

def hex_print(bytes):
  return "0x" + " 0x".join("%02x" % b for b in bytes)



class MessageType(Enum):
  TEXT_MSG = 0
  TEXT_MSG_W_ACK = 1
  SENSOR_DATA = 2
  PING = 3
  ACK = 255

class Priority(Enum):
  NORMAL = 0
  HIGH = 1

class MessageStatus(Enum):
  NEW = 0
  SENT = 1
  REBROADCASTED = 2
  ACK = 3
  NAK = 4
  DONE = 5
  FAILED = 6
  REBROADCASTED_ONCE = 7