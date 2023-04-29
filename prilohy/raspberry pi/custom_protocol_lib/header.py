from custom_protocol_lib.base_utils import *
import random

""" Message header consisting of
2 Bytes destination address
2 Bytes sender address
4 Bytes message id
2 Bytes checksum of first 8 bytes (CRC-16/CCITT-FALSE)
1 Byte message type type MessageType
1 Byte priority
"""

class Header:
  def __init__(self):
    self.destination_address = None
    self.sender_address = None
    self.header = None
    self.priority = None

  def new_header(self, destination_address, sender_address, message_type=MessageType.TEXT_MSG, priority=Priority.NORMAL):
    self.destination_address = destination_address
    self.sender_address = sender_address
    self.message_type = message_type
    self.priority = priority
    self.header = bytearray(HEADER_LENGTH)
    self.__construct_header()
    self.__fill_checksum()

  def __construct_header(self):
    destination = self.destination_address.to_bytes(2, 'big')
    self.header[0] = destination[0]
    self.header[1] = destination[1]

    sender = self.sender_address.to_bytes(2, 'big')
    self.header[2] = sender[0]
    self.header[3] = sender[1]

    self.header[4] = random.randint(0, 255)
    self.header[5] = random.randint(0, 255)
    self.header[6] = random.randint(0, 255)
    self.header[7] = random.randint(0, 255)

    self.header[10] = self.message_type
    self.header[11] = self.priority

  def __fill_checksum(self):
    checksum = calculate_checksum(self.header)
    checksum_bytes = checksum.to_bytes(2, 'big')
    self.header[8] = checksum_bytes[0]
    self.header[9] = checksum_bytes[1]

  def get_header_bytes(self):
    return self.header

  def get_message_id(self):
    return int.from_bytes(self.header[4:8], 'big')

  def get_sender(self):
    return self.sender_address

  def get_priority(self):
    return self.priority

  def get_destination(self):
    return self.destination_address

  def get_message_type(self):
    return self.message_type

  def construct_header_from_bytes(self, bytes_array, override_msg_id=True):
    self.header = bytearray(HEADER_LENGTH)
    self.destination_address = int.from_bytes(bytes_array[:2], 'big')
    self.sender_address = int.from_bytes(bytes_array[2:4], 'big')
    self.message_type = bytes_array[10]
    self.priority = bytes_array[11]
    self.__construct_header()

    if override_msg_id:
      #Important to override messageId and checksum on received messages.
      self.header[4] = bytes_array[4]
      self.header[5] = bytes_array[5]
      self.header[6] = bytes_array[6]
      self.header[7] = bytes_array[7]
      self.header[8] = bytes_array[8]
      self.header[9] = bytes_array[9]

  def construct_raw_packet(self):
    self.message_type = MessageType.RAW_PACKET
