from message import *
from message_queue_item import *

class NodeProcess():
  def __init__(self, rfm9x, notification_callback):
    self.message_queue = {}
    self.rfm9x = rfm9x
    self.notification_callback = notification_callback #TODO used just for testing on armachat devices

  def add_message(self, message_instance: Message, timeout=0, decrement=False, state=None):
    message_id = message_instance.get_message_id()

    if message_id not in self.message_queue:
      message_queue_item = MessageQueueItem(message_instance, timeout)
      if decrement:
        if message_instance.get_message_type() != MessageType.SENSOR_DATA:
          message_queue_item.decrement_maxhop()

      if state is not None:
        message_queue_item.update_message_state(state)
      self.notification_callback(f"Adding message {message_queue_item.get_message_id()} to queue")
      self.message_queue[message_id] = message_queue_item
    #else:
    #TODO Message with same id already exists in queue, dont add it to queue again

  def new_text_message(self, destination_address, string_message, w_ack = False, max_hop=protocol_config.DEFAULT_MAX_HOP, priority=Priority.NORMAL):
    #This method is used only for user created new text messages
    message_instance = Message()
    message_instance.new_text_message(destination_address, protocol_config.MY_ADDRESS, string_message, w_ack, max_hop, priority)

    self.add_message(message_instance)

  def new_sensor_message(self, destination_address, sensor_data, ttl=protocol_config.DEFAULT_TTL, priority=Priority.NORMAL):
    #This method is used only for user created sensor data messages
    message_instance = Message()
    message_instance.new_sensor_message(destination_address, protocol_config.MY_ADDRESS, sensor_data, ttl, priority)

    self.add_message(message_instance)

  def new_traceroute_request(self, destination_address, max_hop=protocol_config.DEFAULT_MAX_HOP, priority=Priority.NORMAL):
    #This method is used only for user created traceroute request messages
    message_instance = Message()
    message_instance.new_traceroute_request(destination_address, protocol_config.MY_ADDRESS, max_hop, priority)

    self.add_message(message_instance)

  def receive_message(self):
    received_packet = self.rfm9x.receive(timeout=0.1) #TODO this timeout is slowing down the main process loop
    if received_packet is not None and len(received_packet) >= protocol_config.HEADER_LENGTH:
      checksum = calculate_checksum(received_packet)
      checksum_bytes = checksum.to_bytes(2, 'big')

      if checksum_bytes[0] != received_packet[8] or checksum_bytes[1] != received_packet[9]:
        #Received packet does not belong to this protocol
        return

      message = Message()
      message.construct_message_from_bytes(received_packet)

      #TODO monitoring mode just for testing
      if protocol_config.MONITORING:
        self.notification_callback("Received, destination:" + str(message.get_destination()))

      if message.get_destination() == protocol_config.MY_ADDRESS:
        #TODO add message to userMessagesList(or Map 🤔?)

        if message.get_header().get_message_type() != MessageType.ACK:
          if message.get_message_id() not in self.message_queue:
            #Success, message arrived to destination
            self.notification_callback("You received new message")

            if message.get_w_ack():
              #Received message requires to send back ACK
              ack_message_instance = Message()
              ack_message_instance.new_ack_message(message.get_sender(), protocol_config.MY_ADDRESS, message.get_message_id(), max_hop=message.get_initialMaxHop(), priority=message.get_header().get_priority())

              #Hardcoded timeout for ACK message
              self.add_message(ack_message_instance, 1500)
            else:
              #Received message does not require to send back ACK
              #But we have to send ACK anyway, so that neighbor node can remove this message from queue and stop rebroadcasting it
              #This ACK message will have maxHop set to 0 so that only neighbor node will receive it
              ack_message_instance = Message()
              ack_message_instance.new_ack_message(message.get_sender(), protocol_config.MY_ADDRESS, message.get_message_id(), max_hop=0)

              #Hardcoded timeout for ACK message
              self.add_message(ack_message_instance, 1500)

            #Add message to queue with state DONE so that it wont be "received" again
            self.add_message(message, 0, True, state=MessageState.DONE)

            if message.get_header().get_message_type() == MessageType.TRACEROUTE_REQUEST:
              #Received traceroute request, send back traceroute response
              traceroute_response_message_instance = Message()
              traceroute_response_message_instance.new_traceroute_message(message.get_sender(), protocol_config.MY_ADDRESS, max_hop=message.get_initialMaxHop(), priority=message.get_header().get_priority())

              self.add_message(traceroute_response_message_instance, 1500)

            return (message, self.rfm9x.last_snr, self.rfm9x.last_rssi) #TODO return used only for testing on armachat devices, returns message which can be displayed on display
        else:
          #Received ACK message
          ack_message_id = message.get_ack_message_id()
          if ack_message_id in self.message_queue:
            if self.message_queue[ack_message_id].get_state() != MessageState.ACK:
              self.notification_callback(f"Received ACK for message {ack_message_id}")
              self.message_queue[ack_message_id].update_message_state(MessageState.ACK)
          return

      else:
        #Received message is not for current node, add it to queue and rebroadcast it or update state
        if message.get_message_id() in self.message_queue:
          message_queue_item = self.message_queue[message.get_message_id()]
          #Received message is already in queue, update state
          if message_queue_item.get_sender() == protocol_config.MY_ADDRESS:
            #Received rebroadcast of message which was created by me. Either update state to rebroadcasted or done based on w_ack
            self.notification_callback(f"Message {message_queue_item.get_message_id()} was rebroadcasted")
            if message_queue_item.get_w_ack():
              message_queue_item.update_message_state(MessageState.REBROADCASTED)
              message_queue_item.set_timeout(protocol_config.ACK_WAIT_TIME*1000)
            else:
              message_queue_item.update_message_state(MessageState.DONE)
          else:
            #Received rebroadcast of message which was created by someone else. Delete this message from queue so that it wont be rebroadcasted by me again
            self.notification_callback(f"Deleting message {message_queue_item.get_message_id()}")
            del self.message_queue[message_queue_item.get_message_id()]
        else:
          #Received message is not in queue, check if its ACK message
          if message.get_message_type() == MessageType.ACK:
            #Received ACK message, delete corresponding message from queue if it exists
            ack_message_id = message.get_ack_message_id()
            if ack_message_id in self.message_queue:
              del self.message_queue[ack_message_id]
              return
          #Received message is not in queue, decrement maxHop/TTL and add it to queue
          if (message.get_message_type() != MessageType.SENSOR_DATA and message.get_maxHop() > 0) or (message.get_message_type() == MessageType.SENSOR_DATA and message.get_ttl() > 0):
            self.add_message(message, self.get_timeout(self.rfm9x.last_snr), True)

  def get_timeout(self, snr, randomize=False):
    #TODO implemenet timeout randomization when enabled in config
    # - this is used when packet cant reach destination because of network topology ( V shape...)
    # Randomization is set globaly in config, but it will reset after reboot. So this config value wont be saved in flash
    if randomize:
      return 150*random.randint(5, 15)

    #This function was generated by chatgpt
    #(e^(0.1 * snr) - e^(-2)) / (e^(2) - e^(-2)) * (6000 - 1000) + 1000
    #Maybe find a better function...

    SNR_min = -20
    SNR_max = 20
    return int(((snr - SNR_min) / (SNR_max - SNR_min)) * 5000)+1000 #Output min: 1000, max: 6000 (with snr range of -20 to 20)

  def tick(self):
    for message_queue_itm in self.message_queue.values():
      if message_queue_itm.get_state() == MessageState.NEW or message_queue_itm.get_state() == MessageState.SENT:
        if message_queue_itm.get_last_millis() + message_queue_itm.get_timeout() < round(time.monotonic() * 1000) or message_queue_itm.get_priority == Priority.HIGH:
          if (message_queue_itm.get_message_type() != MessageType.SENSOR_DATA and message_queue_itm.get_counter() > 0) \
          or (message_queue_itm.get_message_type() == MessageType.SENSOR_DATA and message_queue_itm.get_counter() > 0 and message_queue_itm.get_ttl() > 0): #TODO this is horrible, refactor later
            if message_queue_itm.get_message_type() == MessageType.SENSOR_DATA:
              message_queue_itm.decrement_ttl(round(time.monotonic() * 1000) - message_queue_itm.get_last_millis())

            message_queue_itm.decrement_counter()
            #TODO implemnet CSMA here. If channel is busy, wait for fixed time and try again.
            #Additioanl csmaTimeout variable may be needed, which will be used to skip tick process for some time
            self.rfm9x.send(message_queue_itm.get_message_bytes())
            message_queue_itm.update_last_millis()
            message_queue_itm.set_timeout(protocol_config.RESEND_TIMEOUT*1000) #After first send, the timeout can be 0 as it will not break the flooding. But timeout is set to RESEND_TIMEOUT to prevent rapid spamming of the same message
            if message_queue_itm.get_state() == MessageState.NEW:
              message_queue_itm.update_message_state(MessageState.SENT)
              self.notification_callback("Sent, messageId: " + str(message_queue_itm.get_message_id()))
            else:
              self.notification_callback("Resent, messageId: " + str(message_queue_itm.get_message_id()))
          else:
            #Message failed due to exceeded number of resent attempts
            if message_queue_itm.get_sender() == protocol_config.MY_ADDRESS:
              #Message was created by me, update state to failed or delete, if its ACK message
              if message_queue_itm.get_message_type() == MessageType.ACK or message_queue_itm.get_message_type() == MessageType.TRACEROUTE_REQUEST:
                del self.message_queue[message_queue_itm.get_message_id()]
                return
              else:
                message_queue_itm.update_message_state(MessageState.FAILED)
                self.notification_callback(f"Message {message_queue_itm.get_message_id()} failed to be sent")
            else:
              #Message was created by someone else, delete it from queue
              self.notification_callback(f"Deleting message {message_queue_itm.get_message_id()}")
              del self.message_queue[message_queue_itm.get_message_id()]
      elif message_queue_itm.get_state() == MessageState.REBROADCASTED:
        if message_queue_itm.get_last_millis() + message_queue_itm.get_timeout() < round(time.monotonic() * 1000):
          #Message was rebroadcasted, but ACK was not received in time
          message_queue_itm.update_message_state(MessageState.NAK)