from base_utils import *

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
    pass

  #TODO this for some reason doesnt work on pi pico but works on PC  -> enums are not working correctly?
  #def new_header(self, destination_address, sender_address, message_type=MessageType.TEXT_MSG, priority=Priority.NORMAL):
  def new_header(self, destination_address, sender_address, message_type=0, priority=0):
    self.destination_address = destination_address
    self.sender_address = sender_address
    self.message_type = message_type
    self.priority = priority
    self.header = bytearray(protocol_config.HEADER_LENGTH)
    self.__construct_header()

  def __construct_header(self):
    destination = self.destination_address.to_bytes(2, 'big')
    self.header[0] = destination[0]
    self.header[1] = destination[1]

    sender = self.sender_address.to_bytes(2, 'big')
    self.header[2] = sender[0]
    self.header[3] = sender[1]

    self.header[4] = 0xAA#random.randint(0, 255)
    self.header[5] = 0xBB#random.randint(0, 255)
    self.header[6] = 0xCC#random.randint(0, 255)
    self.header[7] = 0xDD#random.randint(0, 255)

    checksum = calculate_checksum(self.header)
    checksum_bytes = checksum.to_bytes(2, 'big')
    self.header[8] = checksum_bytes[0]
    self.header[9] = checksum_bytes[1]

    self.header[10] = self.message_type
    self.header[11] = self.priority

  def get_header_bytes(self):
    return self.header

  def get_message_key(self):
    return self.destination_address ^ self.sender_address ^ int.from_bytes(self.header[4:8], 'big')

  def get_sender(self):
    return self.sender_address

  def get_destination(self):
    return self.destination_address

  def construct_header_from_bytes(self, bytes_array):
    self.header = bytearray(protocol_config.HEADER_LENGTH)
    self.destination_address = int.from_bytes(bytes_array[:2], 'big')
    self.sender_address = int.from_bytes(bytes_array[2:4], 'big')
    self.message_type = bytes_array[10]
    self.priority = bytes_array[11]
    self.__construct_header()

  def __str__(self) -> str:
    return hex_print(self.header)

  def __repr__(self) -> str:
    out_str = f"""Header:_____________________________________________________________________________
|Destination|   Sender  |      MessageId      |   Checksum  |{fill_spaces("MessageType", 14)}|{fill_spaces("Priority",8)}|
| {hex_print(self.header[:2])} | {hex_print(self.header[2:4])} | {hex_print(self.header[4:8])} |  {hex_print(self.header[8:10])}  |{fill_spaces(MessageType[self.message_type], 14)}|{fill_spaces(Priority[self.priority].name, 8)}|
------------------------------------------------------------------------------------
    """
    return out_str