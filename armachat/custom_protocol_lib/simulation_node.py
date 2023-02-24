from message import *
from message_queue_item import *

class SimulationNode():
  def __init__(self, address):
    self.address = address
    self.neighbors = []
    self.message_queue = []

  def add_message(self, message_object: Message, timeout=0, last_rebroadcast=False):
    self.message_queue.append(MessageQueueItem(message_object, timeout, last_rebroadcast))

  def send_message(self, destination_address, message):
    msg_object = Message()
    msg_object.new_message(destination_address, self.address, message)

    print(f'Node {self.address} sending message to {destination_address}\n')
    #TODO some timeout may be needed here.
    #If node0 sends message two times in a row, other node will receive it and immediately set the state to rebroadcasted.
    self.add_message(msg_object, 400)

  def receive_message(self, bytes, timeout):
    message = Message()
    message.construct_message_from_bytes(bytes)

    if message.get_header().destination_address == self.address:
      print(f'SUCCESS --------------- Node {self.address:01x} received message from {message.header.sender_address}')
      self.message_queue.add_message(message, last_rebroadcast=True)
      return

    if message.get_header().get_message_key() in [msg.get_key() for msg in self.message_queue]:
        for message_queue_itm in self.message_queue:
          if message_queue_itm.get_key() == message.get_header().get_message_key():
            if message_queue_itm.get_state() != MessageStatus.REBROADCASTED:
              message_queue_itm.update_message_state(MessageStatus.REBROADCASTED)
              print(f'Node {self.address:01x} setting state to rebroadcasted')
    else:
      if message.get_max_hop() != 0:
        #Current node received message which is not in message_queue yet and message has available maxhop.
        #=> Add it to message_queue and rebroadcast it after some timeout (snr or random based #TODO implement)
        self.add_message(message, timeout)
        print(f'Node {self.address:01x} received foreign message with maxhop {message.get_max_hop()}')

  def add_neighbor(self, node, timeout=200):
    self.neighbors.append((node, timeout))

  def tick(self):
    for message_queue_itm in self.message_queue:
      if (message_queue_itm.get_state() == MessageStatus.NEW or message_queue_itm.get_state() == MessageStatus.SENT) and message_queue_itm.get_last_millis() + message_queue_itm.get_timeout() < round(time.monotonic() * 1000):
        if message_queue_itm.get_sent_counter() > 0 and message_queue_itm.get_max_hop() > 0:
          message_queue_itm.decrement_maxhop()
          message_queue_itm.decrement_counter()

          print(f'\nNode {self.address:01x} is resending message with maxhop {message_queue_itm.get_max_hop()} and counter {message_queue_itm.counter}')
          for neighbor, timeout in self.neighbors:
            neighbor.receive_message(message_queue_itm.get_message_bytes(), timeout)
          message_queue_itm.update_last_millis()
        else:
          message_queue_itm.update_message_state(MessageStatus.FAILED)
