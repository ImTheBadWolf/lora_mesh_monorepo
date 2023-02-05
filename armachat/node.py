from message import *
from message_queue import *

class Node():
  def __init__(self, address):
    self.address = address
    self.neighbors = []
    self.message_queue = MessageQueue()

  def send_message(self, destination_address, message):
    msg_object = Message()
    msg_object.new_message(destination_address, self.address, message, max_hop=13)
    print(f'Node {self.address} sending message to {destination_address}')
    print()
    self.message_queue.add_message(msg_object)

  def receive_message(self, bytes, snr):
    message = Message()
    message.construct_message_from_bytes(bytes)
    if message.get_header().destination_address == self.address:
      print(f'SUCCESS --------------- Node {self.address:01x} received message from {message.header.sender_address} with snr: {snr}:')
      self.message_queue.add_message(message, snr, True)
      return#TODO send ACK back or rebroadcast it once, to let neighbors know that this message is already received and they dont need to rebroadcast it

    if message.get_header().get_message_key() in [x.key for x in self.message_queue.messages]:
      for msg in self.message_queue.messages:
        if msg.key == message.get_header().get_message_key():
          if msg.state != MessageStatus.REBROADCASTED:
            msg.update_message_state(MessageStatus.REBROADCASTED)
            print(f'Node {self.address:01x} setting state to rebroadcasted')
    else:
      self.message_queue.add_message(message, snr)
      print(f'Node {self.address:01x} received foreign message with snr: {snr}: and maxhop {self.message_queue.messages[-1].maxhop}')

  def add_neighbor(self, node, snr=2):
    self.neighbors.append((node, snr))

  def tick(self):
    for message in self.message_queue.messages:
      if (message.state == MessageStatus.NEW or message.state == MessageStatus.SENT) and message.get_last_millis() + message.get_timeout() < round(time.monotonic() * 1000):
        if message.counter != 0 and message.get_maxhop() != 0:
          destination_address = message.message[:2]
          print(f'\nNode {self.address:01x} is resending message destined to {destination_address} with maxhop {message.get_maxhop()} and counter {message.counter}')

          message.decrement_maxhop()
          message.decrement_counter()
          for neighbor, snr in self.neighbors:
            neighbor.receive_message(message.get_message_bytes(), snr)

          message.update_last_millis()
          message.reset_timeout()
        else:
          message.update_message_state(MessageStatus.FAILED)
