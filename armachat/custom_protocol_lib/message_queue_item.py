import time
from message import Message
from base_utils import *

class MessageQueueItem():
  def __init__(self, message_object: Message, timeout=0, last_rebroadcast=False):
    #If timeout == 0 -> message is newly created and sent from the same node,
    # so no wait timeout (unless csma ? #TODO not implemented yet) before broadcasting it
    self.key = message_object.get_header().get_message_key()
    self.message = message_object.get_message_bytes()
    self.state = MessageStatus.NEW
    self.counter = protocol_config.DEFAULT_RESEND_COUNTER if not last_rebroadcast else 1
    self.maxhop = self.get_maxhop_from_message()
    self.timeout = timeout
    self.last_millis = round(time.monotonic() * 1000)
    self.last_rebroadcast = last_rebroadcast

  def get_maxhop_from_message(self):
    return self.message[protocol_config.HEADER_LENGTH]

  def decrement_maxhop(self):
    #Important to decrement maxhop only in message bytes, not class variable #TODO refactor this shitty hack...
    if not self.last_rebroadcast:
      self.message[protocol_config.HEADER_LENGTH] -= 1
    else:
      self.message[protocol_config.HEADER_LENGTH] = 0

    #TODO move these to another method
    #This happens only once the message is sent for the first time
    if self.state == MessageStatus.NEW:
      self.state = MessageStatus.SENT

  def get_max_hop(self):
    return self.message[protocol_config.HEADER_LENGTH]

  def decrement_counter(self):
    self.counter -= 1

  def get_sent_counter(self):
    return self.counter

  def update_message_state(self, state:MessageStatus):
    self.state = state

  def get_key(self):
    return self.key

  def get_state(self):
    return self.state

  def update_last_millis(self):
    self.last_millis = round(time.monotonic() * 1000)

  def reset_timeout(self):
    self.timeout = 1000; #TODO just for testing

  def get_timeout(self):
    return self.timeout

  def get_message_bytes(self):
    return self.message

  def get_last_millis(self):
    return self.last_millis
