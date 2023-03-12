import time
from message import Message
from base_utils import *

class MessageQueueItem():
  def __init__(self, message_instance:Message, timeout=0):
    #If timeout == 0 -> message is newly created and sent from the same node,
    # so no wait timeout (unless csma ? #TODO not implemented yet) before broadcasting it
    self.message_instance = message_instance
    self.message_id = message_instance.get_message_id()
    self.message_bytes = message_instance.get_message_bytes()
    self.state = MessageState.NEW
    self.counter = protocol_config.RESEND_COUNT
    self.timeout = timeout
    self.last_millis = round(time.monotonic() * 1000)
    self.message_type = message_instance.get_header().get_message_type() #TODO
    self.maxhop = None
    self.ttl = None
    self.priority = message_instance.get_header().get_priority()
    self.setMHTTL()
    self.sender = message_instance.get_sender()
    self.destination = message_instance.get_destination()

  def setMHTTL(self):
    if self.message_type == MessageType.SENSOR_DATA:
      self.ttl = self.get_ttl_from_message_bytes()
    else:
      self.maxhop = self.get_maxhop_from_message_bytes()

  def get_maxhop_from_message_bytes(self):
    return self.message_bytes[protocol_config.HEADER_LENGTH]

  def get_ttl_from_message_bytes(self):
    #TODO implement
    return self.message_bytes[protocol_config.HEADER_LENGTH:protocol_config.HEADER_LENGTH + 2]#TODO check if this is correct

  def decrement_maxhop(self):
    self.message_bytes[protocol_config.HEADER_LENGTH] -= 1
    self.maxhop -= 1

  def decrement_ttl(self, decrement_amount):
    #TODO implement self.message_bytes[protocol_config.HEADER_LENGTH:protocol_config.HEADER_LENGTH + 2] -= decrement_amount
    #self.ttl -= decrement_amount
    pass

  def get_maxhop(self):
    return self.maxhop

  def get_ttl(self):
    return self.ttl

  def decrement_counter(self):
    self.counter -= 1

  def get_counter(self):
    return self.counter

  def update_message_state(self, state:MessageState):
    self.state = state

  def get_message_id(self):
    return self.message_id

  def get_state(self):
    return self.state

  def update_last_millis(self):
    self.last_millis = round(time.monotonic() * 1000)

  def get_timeout(self):
    return self.timeout

  def set_timeout(self, timeout):
    self.timeout = timeout

  def get_message_bytes(self):
    return self.message_bytes

  def get_message_type(self):
    return self.message_type

  def get_priority(self):
    return self.priority

  def get_last_millis(self):
    return self.last_millis

  def get_sender(self):
    return self.sender

  def get_destination(self):
    return self.destination

  def get_w_ack(self):
    return self.message_instance.get_w_ack()