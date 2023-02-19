from base_utils import *
from header import Header

class Message():
  def __init__(self):
    pass

  def new_message(self, destination_address, sender_address, message, message_type=MessageType.TEXT_MSG, max_hop=protocol_config.DEFAULT_MAX_HOP, priority=Priority.NORMAL):
    self.header = Header()
    self.header.new_header(destination_address, sender_address, message_type, priority)

    if message_type == MessageType.TEXT_MSG or message_type == MessageType.TEXT_MSG_W_ACK:
      self.text_message = message
      self.max_hop = max_hop
      self.payload = self.__construct_text_message_payload(message, max_hop)
    elif message_type == MessageType.ACK or message_type == MessageType.PING:
      self.payload = list(bytes(max_hop.to_bytes(1, 'big')))
    else: #TODO implement other message types
      self.payload = bytearray(0)

  def __construct_text_message_payload(self, message, maxHop):
    encrypted_message = bytearray(len(message))
    cipher = aesio.AES(protocol_config.AES_KEY, aesio.MODE_CTR, protocol_config.AES_KEY)
    cipher.encrypt_into(bytes(message, "utf-8"), encrypted_message)
    #TODO just for testing on PC
    #encrypted_message = bytes(message, "utf-8")

    return list(bytes(maxHop.to_bytes(1, 'big'))) + list(encrypted_message)

  def parse_message_from_payload(self):
    cipher = aesio.AES(protocol_config.AES_KEY, aesio.MODE_CTR, protocol_config.AES_KEY)
    input = bytes(self.payload[1:])
    decrypted_message = bytearray(len(input))
    cipher.encrypt_into(input, decrypted_message)

    self.text_message = decrypted_message
    self.max_hop = self.payload[0]

  def get_sender(self):
    return self.header.get_sender()

  def get_destination(self):
    return self.header.get_destination()

  def get_max_hop(self):
    return self.max_hop

  def construct_message_from_bytes(self, bytes_array):
    self.header = Header()
    self.header.construct_header_from_bytes(bytes_array[:protocol_config.HEADER_LENGTH])
    self.payload = bytes_array[protocol_config.HEADER_LENGTH:]
    #TODO get message from payload based on message type + decrypt
    self.parse_message_from_payload()

  def get_text_message(self):
    return self.text_message

  def get_header(self):
    return self.header

  def get_message_bytes(self):
    return self.header.get_header_bytes() + bytearray(self.payload)

  def __str__(self):
    return str(self.header) + " | " + hex_print(self.payload[:1]) + " | " + hex_print(self.payload[1:])

  def __repr__(self):
    out_str = f"""
Message:_____________________________________________________________________________
| Max hop | Encrypted message
|{fill_spaces(str(self.payload[:1]), 9)}| {hex_print(self.payload[1:])}
-------------------------------------------------------------------------------------
    """
    return repr(self.header) + out_str