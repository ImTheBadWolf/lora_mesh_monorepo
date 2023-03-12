from base_utils import *
from header import Header

class Message():
  def __init__(self):
    self.w_ack = False
    self.message_id = None

  def new_text_message(self, destination_address, sender_address, message, w_ack = False, max_hop=protocol_config.DEFAULT_MAX_HOP, priority=Priority.NORMAL):
    #This method is used only for user created new text messages
    message_type = MessageType.TEXT_MSG
    if w_ack:
      message_type = MessageType.TEXT_MSG_W_ACK

    self.header = Header()
    self.header.new_header(destination_address, sender_address, message_type, priority)
    self.text_message = message
    self.maxHop = max_hop
    self.initialMaxHop = max_hop
    self.payload = self.__construct_message_payload(message, message_type)
    self.w_ack = w_ack
    self.message_id = self.header.get_message_id()

  def new_ack_message(self, destination_address, sender_address, message_id, max_hop=protocol_config.DEFAULT_MAX_HOP, priority=Priority.NORMAL):
    self.header = Header()
    self.header.new_header(destination_address, sender_address, MessageType.ACK, priority)
    self.message_id = self.header.get_message_id()
    self.maxHop = max_hop
    self.payload = self.__construct_message_payload(str(message_id), MessageType.ACK)
    self.ack_message_id = message_id

  def __construct_message_payload(self, message, message_type):
    encrypted_message = bytearray(len(message))
    cipher = aesio.AES(protocol_config.AES_KEY, aesio.MODE_CTR, protocol_config.AES_KEY)
    cipher.encrypt_into(bytes(message, "utf-8"), encrypted_message)
    #TODO adding maxhop, initialmaxhop or ttl should be dependent on message type
    if message_type == MessageType.ACK:
      return list(bytes(self.maxHop.to_bytes(1, 'big'))) + list(encrypted_message)
    else:
      return list(bytes(self.maxHop.to_bytes(1, 'big'))) + list(bytes(self.initialMaxHop.to_bytes(1, 'big'))) + list(encrypted_message)

  def construct_message_from_bytes(self, bytes_array):
    self.header = Header()
    self.header.construct_header_from_bytes(bytes_array[:protocol_config.HEADER_LENGTH])
    self.payload = bytes_array[protocol_config.HEADER_LENGTH:]

    self.message_id = self.header.get_message_id()
    self.w_ack = self.header.get_message_type() == MessageType.TEXT_MSG_W_ACK
    self.parse_message_from_payload()

    #################
    #TODO just for testing, adding nodeID to message as a sort of traceroute
    strMyAddress = f'{self.text_message.decode("utf-8")} 0x{protocol_config.MY_ADDRESS:04x} '
    encrypted_messageTMP = bytearray(len(strMyAddress))
    cipher = aesio.AES(protocol_config.AES_KEY, aesio.MODE_CTR, protocol_config.AES_KEY)
    cipher.encrypt_into(bytes(strMyAddress, "utf-8"), encrypted_messageTMP)
    if self.header.get_message_type() == MessageType.ACK:
      self.payload = list(bytes(self.maxHop.to_bytes(1, 'big'))) + list(encrypted_messageTMP)
    else:
      self.payload = list(bytes(self.maxHop.to_bytes(1, 'big'))) + list(bytes(self.initialMaxHop.to_bytes(1, 'big'))) + list(encrypted_messageTMP)
    ######################

    if self.header.get_message_type() == MessageType.ACK:
      #TODO this is horrible
      #str = ''.join(chr(i) for i in self.text_message)
      str = ''
      for i in self.text_message: #This is needed only when "traceroute" is added to the messages
        ch = chr(i)
        if ch == " ":
          break
        str += ch
      self.ack_message_id = int(str)

  def parse_message_from_payload(self):
    #TODO decryption is not needed when the message is not for me. Extract only the maxHop and initialMaxHop/TTL
    cipher = aesio.AES(protocol_config.AES_KEY, aesio.MODE_CTR, protocol_config.AES_KEY)
    if self.header.get_message_type() == MessageType.ACK:
      input = bytes(self.payload[1:])
    else: #TEXT_MSG, TEXT_MSG_W_ACK and SENSOR_DATA have first two bytes for maxHop + initialMaxHop or 2B ttl in sensor data
      input = bytes(self.payload[2:])
    decrypted_message = bytearray(len(input))
    cipher.encrypt_into(input, decrypted_message)

    self.text_message = decrypted_message
    self.maxHop = self.payload[0]
    self.initialMaxHop = self.payload[1]

  def get_message_id(self):
    return self.message_id

  def get_w_ack(self):
    return self.w_ack

  def get_destination(self):
    return self.header.get_destination()

  def get_sender(self):
    return self.header.get_sender()

  def get_maxHop(self):
    return self.maxHop

  def get_initialMaxHop(self):
    return self.initialMaxHop

  def get_text_message(self):
    return self.text_message

  def get_message_type(self):
    return self.header.get_message_type()

  def get_header(self):
    return self.header

  def get_message_bytes(self):
    return self.header.get_header_bytes() + bytearray(self.payload)

  def get_ack_message_id(self):
    return self.ack_message_id