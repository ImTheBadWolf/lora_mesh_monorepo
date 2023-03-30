from base_utils import *
from header import Header

class Message():
  def __init__(self, config, snr=None, rssi=None):
    self.w_ack = False
    self.message_id = None
    self.config = config
    self.text_message = None
    self.sensor_data = None
    self.initialMaxHop = None
    self.snr = snr
    self.rssi = rssi
    self.lora_config = "Bw500Cr45Sf128"  #TODO add loraconfig from config here

  def new_text_message(self, destination_address, sender_address, message, w_ack = False, max_hop=None, priority=Priority.NORMAL):
    #This method is used only for user-created new text messages
    if max_hop is None:
      max_hop = self.config.DEFAULT_MAX_HOP
    message_type = MessageType.TEXT_MSG
    if w_ack:
      message_type = MessageType.TEXT_MSG_W_ACK

    self.header = Header()
    self.header.new_header(destination_address, sender_address, message_type, priority)

    self.text_message = bytes(message[:238], "utf-8")
    self.maxHop = max_hop
    self.initialMaxHop = max_hop
    self.payload = self.__construct_message_payload(message, message_type)
    self.w_ack = w_ack
    self.message_id = self.header.get_message_id()

  def new_ack_message(self, destination_address, sender_address, message_id, max_hop=None, priority=Priority.NORMAL):
    if max_hop is None:
      max_hop = self.config.DEFAULT_MAX_HOP
    self.header = Header()
    self.header.new_header(destination_address, sender_address, MessageType.ACK, priority)

    self.message_id = self.header.get_message_id()
    self.maxHop = max_hop
    self.payload = self.__construct_message_payload(str(message_id), MessageType.ACK)
    self.ack_message_id = message_id

  def new_sensor_message(self, destination_address, sender_address, sensor_data, ttl=None, priority=Priority.NORMAL):
    if ttl is None:
      ttl = self.config.DEFAULT_TTL
    self.header = Header()
    self.header.new_header(destination_address, sender_address, MessageType.SENSOR_DATA, priority)

    self.sensor_data = sensor_data[:238]
    self.ttl = ttl
    self.message_id = self.header.get_message_id()
    self.payload = self.__construct_message_payload(str(sensor_data), MessageType.SENSOR_DATA)

  def new_traceroute_request(self, destination_address, sender_address, max_hop=None, priority=Priority.NORMAL):
    if max_hop is None:
      max_hop = self.config.DEFAULT_MAX_HOP
    self.header = Header()
    self.header.new_header(destination_address, sender_address, MessageType.TRACEROUTE_REQUEST, priority)

    self.maxHop = max_hop
    self.initialMaxHop = max_hop
    self.message_id = self.header.get_message_id()
    self.payload = self.__construct_message_payload("", MessageType.TRACEROUTE_REQUEST)

  def new_traceroute_message(self, destination_address, sender_address, max_hop=None, priority=Priority.NORMAL):
    if max_hop is None:
      max_hop = self.config.DEFAULT_MAX_HOP
    self.header = Header()
    self.header.new_header(destination_address, sender_address, MessageType.TRACEROUTE, priority)

    self.maxHop = max_hop
    self.message_id = self.header.get_message_id()
    self.payload = self.__construct_message_payload(f"0x{sender_address:04x}", MessageType.TRACEROUTE)

  def __construct_message_payload(self, message, message_type):
    encrypted_message = bytearray(len(message))
    cipher = aesio.AES(self.config.AES_KEY, aesio.MODE_CTR, self.config.AES_KEY)
    cipher.encrypt_into(bytes(message, "utf-8"), encrypted_message)

    if message_type == MessageType.ACK or message_type == MessageType.TRACEROUTE:
      #ACK and TRACEROUTE messages are not encrypted
      return list(bytes(self.maxHop.to_bytes(1, 'big'))) + list(bytes(message, "utf-8"))
    elif message_type == MessageType.SENSOR_DATA:
      return list(bytes(self.ttl.to_bytes(2, 'big'))) + list(encrypted_message)
    else: #text_msg or text_msg_wack or traceroute_request
      return list(bytes(self.maxHop.to_bytes(1, 'big'))) + list(bytes(self.initialMaxHop.to_bytes(1, 'big'))) + list(encrypted_message)

  def construct_message_from_bytes(self, bytes_array):
    self.header = Header()
    self.header.construct_header_from_bytes(bytes_array[:HEADER_LENGTH])
    self.payload = bytes_array[HEADER_LENGTH:]

    self.message_id = self.header.get_message_id()
    self.w_ack = self.header.get_message_type() == MessageType.TEXT_MSG_W_ACK
    self.parse_message_from_payload()

    if self.header.get_message_type() == MessageType.TRACEROUTE:
      #Adding my address to the traceroute message
      strMyAddress = f'{self.text_message.decode("utf-8")}=>0x{self.config.MY_ADDRESS:04x}'
      self.payload = list(bytes(self.maxHop.to_bytes(1, 'big'))) + list(bytes(strMyAddress, "utf-8"))
      self.text_message = bytes(strMyAddress, "utf-8")

    if self.header.get_message_type() == MessageType.ACK:
      #Get the message id this ACK packet is confirming
      str = ''.join(chr(i) for i in self.text_message)
      self.ack_message_id = int(str)

  def parse_message_from_payload(self):
    if self.header.get_message_type() == MessageType.TEXT_MSG_W_ACK or self.header.get_message_type() == MessageType.TEXT_MSG or self.header.get_message_type() == MessageType.TRACEROUTE_REQUEST:
      self.maxHop = self.payload[0]
      self.initialMaxHop = self.payload[1]
    elif self.header.get_message_type() == MessageType.SENSOR_DATA:
      self.ttl = int.from_bytes(bytes(self.payload[:2]), 'big')
    else: #ACK or TRACEROUTE
      self.maxHop = self.payload[0]
      #ACK and TRACEROUTE messages are not encrypted
      self.text_message = self.payload[1:]

    if self.get_destination() == self.config.MY_ADDRESS:
      cipher = aesio.AES(self.config.AES_KEY, aesio.MODE_CTR, self.config.AES_KEY)
      input = bytes(self.payload[2:])
      decrypted_message = bytearray(len(input))
      cipher.encrypt_into(input, decrypted_message)

      if self.header.get_message_type() == MessageType.TEXT_MSG_W_ACK or self.header.get_message_type() == MessageType.TEXT_MSG or self.header.get_message_type() == MessageType.TRACEROUTE_REQUEST:
        try:
          decrypted_message.decode("utf-8")
          self.text_message = decrypted_message
        except:
          #Received message was encrypted using different aes key
          self.text_message = bytes("&lt;ENCRYPTED&gt;", "utf-8")

      elif self.header.get_message_type() == MessageType.SENSOR_DATA:
        try:
          decrypted_message.decode("utf-8")
          self.sensor_data = decrypted_message
        except:
          #Received message was encrypted using different aes key
          self.sensor_data = bytes("&lt;ENCRYPTED&gt;", "utf-8")

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
    if self.text_message is None:
      return 0
    return self.initialMaxHop

  def get_ttl(self):
    return self.ttl

  def get_text_message(self):
    if self.text_message is None:
      return bytes("", "utf-8")
    return self.text_message

  def get_sensor_data(self):
    if self.sensor_data is None:
      return bytes("", "utf-8")
    return self.sensor_data

  def get_message_type(self):
    return self.header.get_message_type()

  def get_header(self):
    return self.header

  def get_message_bytes(self):
    return self.header.get_header_bytes() + bytearray(self.payload)

  def get_ack_message_id(self):
    return self.ack_message_id

  def get_packet_info(self):
    return (self.snr, self.rssi, self.lora_config)