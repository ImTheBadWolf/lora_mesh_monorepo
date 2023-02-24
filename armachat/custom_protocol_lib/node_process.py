from message import *
from message_queue_item import *

class NodeProcess():
  def __init__(self, rfm9x, notification_callback):
    self.message_queue = []
    self.rfm9x = rfm9x
    self.notification_callback = notification_callback #TODO used just for testing on armachat devices

  #TODO
  def add_message(self, message_object: Message, timeout=0, last_rebroadcast=False):
    self.message_queue.append(MessageQueueItem(message_object, timeout, last_rebroadcast))

  def send_message(self, destination_address, string_message):
    msg_object = Message()
    msg_object.new_message(destination_address, protocol_config.MY_ADDRESS, string_message)

    self.rfm9x.send(msg_object.get_message_bytes())
    self.add_message(msg_object)
    self.notification_callback("Sent")

  def receive_message(self):
    received_packet = self.rfm9x.receive(timeout=0.1)
    if received_packet is not None:
      message = Message()
      message.construct_message_from_bytes(received_packet)

      #TODO monitoring mode just for testing
      if protocol_config.MONITORING:
        self.notification_callback("Received, destination:" + str(message.get_destination()))

      if message.get_destination() == protocol_config.MY_ADDRESS:
        #Success, message arrived to destination
        self.notification_callback("You received new message")

        #Rebroadcast received message with maxHop = 0, to let neighbor nodes know that message was received,
        # and they dont need to rebroadcast it
        self.add_message(message, last_rebroadcast=True)
        return (message, self.rfm9x.last_snr, self.rfm9x.last_rssi)

      if message.get_header().get_message_key() in [msg.get_key() for msg in self.message_queue]:
        for message_queue_itm in self.message_queue:
          if message_queue_itm.get_key() == message.get_header().get_message_key():
            if message_queue_itm.get_state() != MessageStatus.REBROADCASTED:
              #Received rebroadcast of message which is in message_queue (from another node)
              #=> updating state to rebroadcasted, so that current node wont rebroadcast it again
              message_queue_itm.update_message_state(MessageStatus.REBROADCASTED)
      else:
        if message.get_max_hop() != 0:
          #Current node received message which is not in message_queue yet and message has available maxhop.
          #=> Add it to message_queue and rebroadcast it after some timeout (snr or random based #TODO implement)
          self.add_message(message, self.get_timeout(self.rfm9x.last_snr))
    return None

  def get_timeout(self, snr, randomize=False):
    #TODO #TODO relation between snr and timeout. Bulgarian constant *30 for now... or forever
    #TODO implemenet timeout randomization when enabled
    # - this is used when packet cant reach destination because of network topology ( V shape...)
    # Randomization is set per-message
    #return 30*random.randint(1, 15)
    return 30*snr

  def tick(self):
    for message_queue_itm in self.message_queue:
      if (message_queue_itm.get_state() == MessageStatus.NEW or message_queue_itm.get_state() == MessageStatus.SENT) and message_queue_itm.get_last_millis() + message_queue_itm.get_timeout() < round(time.monotonic() * 1000):
        if message_queue_itm.get_sent_counter() > 0 and message_queue_itm.get_max_hop() > 0:
          #Message is in message_queue and wait timeout has passed.
          #Maxhop and sent-counter (number of times the message can be sent) is not 0 =>  rebroadcast it
          message_queue_itm.decrement_maxhop()
          message_queue_itm.decrement_counter()

          self.rfm9x.send(message_queue_itm.get_message_bytes())

          message_queue_itm.update_last_millis()
          #message_queue_itm.reset_timeout() #TODO maybe set timeout to 0 after the first rebroadcast.
          # Timeout should be needed only For first rebroadcast to secure that the message is rebroadcasted from the farthest away node.
          # After that the timeout could be removed probably?? #TODO #TODO
        else:
          #Message is in message_queue and wait timeout has passed but there is no more maxhop available
          #or the message has already been sent the maximum number of times.
          message_queue_itm.update_message_state(MessageStatus.FAILED)
