import time
from message import Message
from base_utils import *

class MessageQueueItem():
  def __init__(self, message_object: Message, snr, last_rebroadcast):
    self.key = message_object.get_header().get_message_key()
    self.message = message_object.get_message_bytes()
    self.state = MessageStatus.NEW
    self.counter = protocol_config.DEFAULT_RESEND_COUNTER if not last_rebroadcast else 1
    self.snr = snr
    self.maxhop = self.get_maxhop_from_message()
    self.timeout = self.__calculate_timeout()
    self.last_millis = round(time.monotonic() * 1000)
    self.last_rebroadcast = last_rebroadcast

  def get_maxhop_from_message(self):
    return self.message[protocol_config.HEADER_LENGTH]

  def decrement_maxhop(self):
    #Important to decrement maxhop only in message bytes, not class variable
    if not self.last_rebroadcast:
      self.message[protocol_config.HEADER_LENGTH] -= 1
    else:
      self.message[protocol_config.HEADER_LENGTH] = 0

    #TODO move these to another method
    if self.state == MessageStatus.NEW:
      self.state = MessageStatus.SENT

  def get_maxhop(self):
    return self.message[protocol_config.HEADER_LENGTH]

  def decrement_counter(self):
    self.counter -= 1

  def update_message_state(self, state:MessageStatus):
    self.state = state

  def __calculate_timeout(self):
    #TODO implemenet timeout randomization when enabled
    #return 30*random.randint(1, 15)
    return 30*self.snr

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

class MessageQueue():
  def __init__(self):
    self.messages = []

  def add_message(self, message_object: Message, snr=0, last_rebroadcast=False):
    #If snr == 0 -> message is newly created and sent on the same node, so no timeout (unless csma)
    self.messages.append(MessageQueueItem(message_object, snr, last_rebroadcast))
