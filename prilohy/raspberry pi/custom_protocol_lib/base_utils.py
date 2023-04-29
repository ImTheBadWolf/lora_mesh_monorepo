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

def get_string_msg_type(msg_type):
  if msg_type == MessageType.TEXT_MSG:
    return "TEXT"
  elif msg_type == MessageType.TEXT_MSG_W_ACK:
    return "WACK_TEXT"
  elif msg_type == MessageType.SENSOR_DATA:
    return "SENSOR"
  elif msg_type == MessageType.TRACEROUTE:
    return "TRACEROUTE"
  elif msg_type == MessageType.TRACEROUTE_REQUEST:
    return "TRACEROUTE_REQUEST"
  elif msg_type == MessageType.ACK:
    return "ACK"
  elif msg_type == MessageType.RAW_PACKET:
    return "RAW_PACKET"
  else:
    return "TEXT"

def get_string_msg_state(msg_state):
  if msg_state == MessageState.DONE:
    return "DONE"
  elif msg_state == MessageState.REBROADCASTED:
    return "REBROADCASTED"
  elif msg_state == MessageState.ACK:
    return "ACK"
  elif msg_state == MessageState.NAK:
    return "NAK"
  elif msg_state == MessageState.FAILED:
    return "FAILED"
  elif msg_state == MessageState.DELETED:
    return "DELETED"
  elif msg_state == MessageState.NEW:
    return "NEW"
  elif msg_state == MessageState.SENT:
    return "SENT"
  else:
    return "DONE"

def parse_hex_address(intAddres):
  stringAddress = f"{intAddres:04x}"
  return f"0x{stringAddress.upper()}"

def parse_messages(messageList, config):
  message_entity_list = []
  for message_queue_item in messageList:
    message_entity = {}

    message_entity['id'] = message_queue_item.get_message_id()
    message_entity['order'] = message_queue_item.get_message_counter()
    lora_info = message_queue_item.get_packet_info()
    message_entity['lora_info'] = {
      'snr': lora_info[0],
      'rssi': lora_info[1],
      'lora_config': lora_info[2]
    }

    if message_queue_item.get_message_type() == MessageType.RAW_PACKET:
      message_entity['payload'] = "Raw packet: " + hex_print(message_queue_item.get_message_bytes())
    else:
      message_entity['from'] = parse_hex_address(message_queue_item.get_sender())
      message_entity['to'] = parse_hex_address(message_queue_item.get_destination())
      msg_type = message_queue_item.get_message_type()
      msg_instance = message_queue_item.get_message_instance()
      message_entity['msg_type'] = get_string_msg_type(msg_type)
      try:
        if msg_type == MessageType.SENSOR_DATA:
          message_entity['payload'] = msg_instance.get_sensor_data().decode("utf-8")
        else:
          message_entity['payload'] = msg_instance.get_text_message().decode("utf-8")
      except:
        message_entity['payload'] = hex_print(message_queue_item.get_message_bytes())

      if (msg_type == MessageType.TEXT_MSG or msg_type == MessageType.TEXT_MSG_W_ACK) and message_queue_item.get_sender() != config.MY_ADDRESS:
        message_entity['hop_count'] = msg_instance.get_initialMaxHop() - msg_instance.get_maxHop()

      if message_queue_item.get_sender() == config.MY_ADDRESS:
        message_entity['state'] = get_string_msg_state(message_queue_item.get_state())

    message_entity_list.append(message_entity)
  return message_entity_list

def parse_message_queue(message_queue):
  message_entity_list = []
  for message_queue_item in message_queue.values():
    message_entity = {}

    message_entity['id'] = message_queue_item.get_message_id()
    message_entity['message_bytes'] = hex_print(message_queue_item.get_message_bytes())
    message_entity['state'] = get_string_msg_state(message_queue_item.get_state())
    message_entity['order'] = message_queue_item.get_message_counter()
    lora_info = message_queue_item.get_packet_info()
    message_entity['lora_info'] = {
      'snr': lora_info[0],
      'rssi': lora_info[1],
      'lora_config': lora_info[2]
    }
    message_entity['msg_type'] = get_string_msg_type(message_queue_item.get_message_type())

    if message_queue_item.get_message_type() != MessageType.RAW_PACKET:
      message_entity['from'] = parse_hex_address(message_queue_item.get_sender())
      message_entity['to'] = parse_hex_address(message_queue_item.get_destination())

      msg_type = message_queue_item.get_message_type()
      msg_instance = message_queue_item.get_message_instance()
      if msg_type == MessageType.SENSOR_DATA:
        message_entity['payload'] = msg_instance.get_sensor_data().decode("utf-8")
        message_entity['ttl'] = message_queue_item.get_ttl()
      else:
        message_entity['payload'] = msg_instance.get_text_message().decode("utf-8")
        message_entity['max_hop'] = message_queue_item.get_maxhop()
        message_entity['initial_max_hop'] = msg_instance.get_initialMaxHop()

      message_entity['last_millis'] = message_queue_item.get_last_millis()
      message_entity['timeout'] = message_queue_item.get_timeout()
      message_entity['retry_counter'] = message_queue_item.get_counter()
      message_entity['priority'] = message_queue_item.get_priority()

    message_entity_list.append(message_entity)
  return message_entity_list

class Enum():
  def __init__(self, tupleItems):
    self.tupleItems = tupleItems

  def __getattr__(self, item):
    return self.tupleItems.index(item)

MessageType = Enum(('ACK', 'TEXT_MSG', 'TEXT_MSG_W_ACK', 'SENSOR_DATA', 'TRACEROUTE_REQUEST', 'TRACEROUTE', 'RAW_PACKET'))
Priority = Enum(('NORMAL', 'HIGH'))
MessageState = Enum(('NEW', 'SENT', 'REBROADCASTED', 'ACK', 'NAK', 'DONE', 'FAILED', 'DELETED'))

MESSAGE_QUEUE_SIZE = 100
HEADER_LENGTH = 12