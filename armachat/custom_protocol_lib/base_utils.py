import random
from binascii import hexlify
import protocol_config
import aesio

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
  return "" + ",".join("%02x" % b for b in bytes)

class Enum():
  def __init__(self, tupleItems):
    self.tupleItems = tupleItems

  def __getattr__(self, item):
    return self.tupleItems.index(item)

MessageType = Enum(('ACK', 'TEXT_MSG', 'TEXT_MSG_W_ACK', 'SENSOR_DATA', 'TRACEROUTE_REQUEST', 'TRACEROUTE'))
Priority = Enum(('NORMAL', 'HIGH'))
MessageState = Enum(('NEW', 'SENT', 'REBROADCASTED', 'ACK', 'NAK', 'DONE', 'FAILED', 'DELETED'))