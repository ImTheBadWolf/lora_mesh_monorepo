import gc
from message import *
from message_queue_item import *
from base_utils import *

class NodeProcess():
  def __init__(self, rfm9x, notification_callback, config):
    self.message_queue = {}
    self.message_counter = 0
    self.config = config
    self.rfm9x = rfm9x
    self.notification_callback = notification_callback #TODO used just for testing on armachat devices
    self.latest_message = None

    #TODO just for testing
    self.received_counter = 0
    self.sent_counter = 0

  def add_message(self, message_instance: Message, timeout=0, decrement=False, state=None):
    message_id = message_instance.get_message_id()

    if message_id not in self.message_queue:
      #Check if the queue doesnt have too many messages, if yes delete the oldest one
      #Check only messages that the user can see (text messages, sensor data, traceroute, raw_packet)
      filtered_messages = [(msgId, msg) for msgId, msg in self.message_queue.items() if (self.message_queue[msgId].get_message_type() >= 1 and self.message_queue[msgId].get_message_type() <= 3) or self.message_queue[msgId].get_message_type() == MessageType.TRACEROUTE or self.message_queue[msgId].get_message_type() == MessageType.RAW_PACKET]
      if len(filtered_messages) >= MESSAGE_QUEUE_SIZE:
        #filter messageid of the oldest message from queue based on message_counter get_message_counter()
        oldest_message_id, oldest_message = min(filtered_messages, key=lambda x: x[1].get_message_counter())
        self.notification_callback(f"Removing oldset message id:{oldest_message_id} from queue")
        del self.message_queue[oldest_message_id]
      gc.collect()

      message_queue_item = MessageQueueItem(message_instance, self.message_counter, self.config, timeout)
      self.message_counter += 1
      if decrement:
        if message_instance.get_message_type() != MessageType.SENSOR_DATA:
          message_queue_item.decrement_maxhop()
        else:
          message_queue_item.decrement_ttl(200)

      if state is not None:
        message_queue_item.update_message_state(state)
      if state != MessageState.DONE:
        self.notification_callback(f"Adding message {message_queue_item.get_message_id()} to queue")
      self.message_queue[message_id] = message_queue_item
    #else:
    #TODO Message with same id already exists in queue, dont add it to queue again

  def new_text_message(self, destination_address, string_message, w_ack = False, max_hop=None, priority=Priority.NORMAL):
    #This method is used only for user created new text messages
    if max_hop is None:
      max_hop = self.config.DEFAULT_MAX_HOP
    message_instance = Message(self.config)
    message_instance.new_text_message(destination_address, self.config.MY_ADDRESS, string_message, w_ack, max_hop, priority)

    self.add_message(message_instance)
    self.sent_counter += 1
    gc.collect()

  def new_sensor_message(self, destination_address, sensor_data, ttl=None, priority=Priority.NORMAL):
    #This method is used only for user created sensor data messages
    if ttl is None:
      ttl = self.config.DEFAULT_TTL
    message_instance = Message(self.config)
    message_instance.new_sensor_message(destination_address, self.config.MY_ADDRESS, sensor_data, ttl, priority)

    self.add_message(message_instance)
    gc.collect()

  def new_traceroute_request(self, destination_address, max_hop=None, priority=Priority.NORMAL):
    #This method is used only for user created traceroute request messages
    if max_hop is None:
      max_hop = self.config.DEFAULT_MAX_HOP
    message_instance = Message(self.config)
    message_instance.new_traceroute_request(destination_address, self.config.MY_ADDRESS, max_hop, priority)

    self.add_message(message_instance)
    gc.collect()

  def resend_text_message(self, message_id):
    if message_id not in self.message_queue:
      return
    message_queue_item = self.message_queue[message_id]
    message_instance = Message(self.config)
    message_instance.new_text_message(message_queue_item.get_destination(), self.config.MY_ADDRESS, message_queue_item.get_message_instance().get_text_message().decode("utf-8"), message_queue_item.get_w_ack(), message_queue_item.get_maxhop(), message_queue_item.get_priority())

    self.add_message(message_instance)
    gc.collect()

  def get_latest_message(self):
    return self.latest_message

  def receive_message(self):
    received_packet = self.rfm9x.receive(timeout=25)
    if received_packet is not None and len(received_packet) >= HEADER_LENGTH:
      checksum = calculate_checksum(received_packet)
      checksum_bytes = checksum.to_bytes(2, 'big')

      if checksum_bytes[0] != received_packet[8] or checksum_bytes[1] != received_packet[9]:
        #Received packet does not belong to this protocol
        if self.config.MONITORING_ENABLED:
          message = Message(self.config, self.rfm9x.last_snr, self.rfm9x.last_rssi)
          message.construct_raw_packet(received_packet)
          self.notification_callback("Received raw packet, msgId: " + str(message.get_message_id()))
          self.add_message(message, 0, False, state=MessageState.DONE)
        return

      message = Message(self.config, self.rfm9x.last_snr, self.rfm9x.last_rssi)
      message.construct_message_from_bytes(received_packet)

      if message.get_destination() == self.config.MY_ADDRESS:
        if message.get_header().get_message_type() != MessageType.ACK:
          if message.get_message_id() not in self.message_queue:
            #Success, message arrived to destination
            self.notification_callback("You received new message, msgId: " + str(message.get_message_id()))

            if message.get_w_ack():
              #Received message requires to send back ACK
              ack_message_instance = Message(self.config)
              ack_message_instance.new_ack_message(message.get_sender(), self.config.MY_ADDRESS, message.get_message_id(), max_hop=message.get_initialMaxHop(), priority=message.get_header().get_priority())
              self.notification_callback(f"Created ACK message(id: {ack_message_instance.get_message_id()}), confirming msgID: {message.get_message_id()}, maxHop={ack_message_instance.get_maxHop()}")
              #Hardcoded timeout for ACK message
              self.add_message(ack_message_instance, 1500)
            else:
              #Received message does not require to send back ACK
              #But we have to send ACK anyway, so that neighbor nodes can remove this message from queue and stop rebroadcasting it
              #This ACK message will have maxHop set to 0 so that only neighbor nodes will receive it
              ack_message_instance = Message(self.config)
              ack_message_instance.new_ack_message(message.get_sender(), self.config.MY_ADDRESS, message.get_message_id(), max_hop=0)
              self.notification_callback(f"Created ACK message(id: {ack_message_instance.get_message_id()}), confirming msgID: {message.get_message_id()}, maxHop={ack_message_instance.get_maxHop()}")
              #Hardcoded timeout for ACK message
              self.add_message(ack_message_instance, 1500)

            #Add message to queue with state DONE so that it wont be "received" again
            #State DONE is needed only for messages visible to user, so messages of type TRACE_ROUTE_REQUEST wont have state DONE, they can be deleted
            if message.get_header().get_message_type() == MessageType.TRACEROUTE_REQUEST:
              self.add_message(message, 0, True, state=MessageState.DELETED)
              message_queue_item = self.message_queue[message.get_message_id()]
              message_queue_item.update_last_millis()
              message_queue_item.set_timeout(self.config.DELETE_WAIT_TIME*1000)
            else:
              self.received_counter += 1
              self.add_message(message, 0, True, state=MessageState.DONE)

            if message.get_header().get_message_type() == MessageType.TRACEROUTE_REQUEST:
              #Received traceroute request, send back traceroute response
              traceroute_response_message_instance = Message(self.config)
              traceroute_response_message_instance.new_traceroute_message(message.get_sender(), self.config.MY_ADDRESS, max_hop=message.get_initialMaxHop(), priority=message.get_header().get_priority())

              self.add_message(traceroute_response_message_instance, 2500)

            self.latest_message = (message, self.rfm9x.last_snr, self.rfm9x.last_rssi)
        else:
          #Received ACK message
          ack_message_id = message.get_ack_message_id()
          if ack_message_id in self.message_queue:
            message_queue_item = self.message_queue[ack_message_id]
            if message_queue_item.get_state() != MessageState.ACK:
              self.notification_callback(f"Received ACK for message {ack_message_id}")

              #If its traceroute message, set state to deleted. Sensor messages could be also deleted, as sensors dont care if they receive ACK or not
              if message_queue_item.get_message_type() == MessageType.TRACEROUTE or message_queue_item.get_message_type() == MessageType.SENSOR_DATA:
                message_queue_item.update_message_state(MessageState.DELETED)
                message_queue_item.update_last_millis()
                message_queue_item.set_timeout(self.config.DELETE_WAIT_TIME*1000)
              else:
                message_queue_item.update_message_state(MessageState.ACK)
      else:
        #Received message is not for current node, add it to queue and rebroadcast it or update state
        if message.get_message_id() in self.message_queue:
          message_queue_item = self.message_queue[message.get_message_id()]
          #Received message is already in queue, update state
          if message_queue_item.get_sender() == self.config.MY_ADDRESS:
            #Received rebroadcast of message which was created by me. Either update state to rebroadcasted or done based on w_ack
            self.notification_callback(f"Message {message_queue_item.get_message_id()} was rebroadcasted")
            if message_queue_item.get_w_ack():
              if message_queue_item.get_state() != MessageState.ACK:
                message_queue_item.update_message_state(MessageState.REBROADCASTED)
              message_queue_item.update_last_millis()
              message_queue_item.set_timeout(self.config.ACK_WAIT_TIME*1000)
            else:
              #Only update state to DONE for user visible messages (TEXT), other messages can be deleted
              if message_queue_item.get_message_type() == MessageType.TEXT_MSG or message_queue_item.get_message_type() == MessageType.TEXT_MSG_W_ACK:
                message_queue_item.update_message_state(MessageState.DONE)
              else:
                message_queue_item.update_message_state(MessageState.DELETED)
                message_queue_item.update_last_millis()
                message_queue_item.set_timeout(self.config.DELETE_WAIT_TIME*1000)
          else:
            #Received rebroadcast of message which was created by someone else. Delete this message from queue so that it wont be rebroadcasted by me again
            #Only delete if the maxhop/ttl is less or equal to current node's maxhop/ttl
            should_delete = False
            if message_queue_item.get_message_type() == MessageType.SENSOR_DATA:
              if message.get_ttl() <= message_queue_item.get_ttl():
                should_delete = True
            else:
              if message.get_maxHop() <= message_queue_item.get_maxhop():
                should_delete = True

            if should_delete:
              message_queue_item.update_message_state(MessageState.DELETED)
              message_queue_item.update_last_millis()
              message_queue_item.set_timeout(self.config.DELETE_WAIT_TIME*1000)
        else:
          #Received message is not in queue, check if its ACK message
          if message.get_message_type() == MessageType.ACK:
            #Received ACK message, delete corresponding message from queue if it exists
            ack_message_id = message.get_ack_message_id()
            if ack_message_id in self.message_queue:
              message_queue_item = self.message_queue[ack_message_id]
              message_queue_item.update_message_state(MessageState.DELETED)
              message_queue_item.update_last_millis()
              message_queue_item.set_timeout(self.config.DELETE_WAIT_TIME*1000)
              return
          #Received message is not in queue. Check if it isnt broadcast message, decrement maxHop/TTL and add it to queue
          if message.get_destination() == self.config.BROADCAST_ADDRESS:
            #It is broadcast message. Add it to user messages
            self.notification_callback("Received new BROADCAST message, msgId: " + str(message.get_message_id()))
            #Add message to queue with state DONE so that it wont be "received" again
            #We have to create another copy of the received message, so that it will have different ID
            #This is needed because one copy of the message will be rebrodcasted further, while the other copy will be displayed to user as received message
            message_copy = Message(self.config, self.rfm9x.last_snr, self.rfm9x.last_rssi)
            message_copy.construct_message_from_bytes(received_packet, override_msg_id=False)
            self.received_counter += 1
            self.add_message(message_copy, 0, False, state=MessageState.DONE)
            self.latest_message = (message, self.rfm9x.last_snr, self.rfm9x.last_rssi)

          if (message.get_message_type() != MessageType.SENSOR_DATA and message.get_maxHop() > 0) or (message.get_message_type() == MessageType.SENSOR_DATA and message.get_ttl() > 0):
            self.add_message(message, self.get_timeout(self.rfm9x.last_snr), True)

  def get_timeout(self, snr):
    #TODO implemenet timeout randomization when enabled in config
    # - this is used when packet cant reach destination because of network topology ( V shape...)
    # Randomization is set globaly in config, but it will reset after reboot. So this config value wont be saved in flash
    if self.config.RANDOMIZE_PATH:
      return 150*random.randint(5, 15)

    #This function was generated by chatgpt
    #(e^(0.1 * snr) - e^(-2)) / (e^(2) - e^(-2)) * (6000 - 1000) + 1000
    #Maybe find a better function...

    SNR_min = -20
    SNR_max = 20
    return int(((snr - SNR_min) / (SNR_max - SNR_min)) * 5000)+1000 #Output min: 1000, max: 6000 (with snr range of -20 to 20)

  def tick(self):
    self.latest_message = None
    self.receive_message()

    for message_queue_itm in self.message_queue.copy().values():
      if message_queue_itm.get_state() == MessageState.NEW or message_queue_itm.get_state() == MessageState.SENT:
        if message_queue_itm.get_last_millis() + message_queue_itm.get_timeout() < round(time.monotonic() * 1000) or message_queue_itm.get_priority() == Priority.HIGH:
          if (message_queue_itm.get_message_type() != MessageType.SENSOR_DATA and message_queue_itm.get_counter() > 0) \
          or (message_queue_itm.get_message_type() == MessageType.SENSOR_DATA and message_queue_itm.get_counter() > 0 and message_queue_itm.get_ttl() > 0):
            if message_queue_itm.get_message_type() == MessageType.SENSOR_DATA:
              message_queue_itm.decrement_ttl(round(time.monotonic() * 1000) - message_queue_itm.get_last_millis())
            if not self.rfm9x.rx_detected():
              try:
                self.rfm9x.send(message_queue_itm.get_message_bytes())
                message_queue_itm.update_last_millis()
                message_queue_itm.set_timeout(self.config.RESEND_TIMEOUT*1000 + random.randint(0, 1000)) #After first send, the timeout can be 0 as it will not break the flooding. But timeout is set to RESEND_TIMEOUT to prevent rapid spamming of the same message
                message_queue_itm.decrement_counter()
                if message_queue_itm.get_state() == MessageState.NEW:
                  message_queue_itm.update_message_state(MessageState.SENT)
                  self.notification_callback("Sent, messageId: " + str(message_queue_itm.get_message_id()))
                else:
                  self.notification_callback("Resent, messageId: " + str(message_queue_itm.get_message_id()))
              except Exception as e:
                print("RFM9x send failed")
                print(e)
            else:
              #Channel is busy, wait for fixed time and try again
              message_queue_itm.update_last_millis()
              message_queue_itm.set_timeout(self.config.CSMA_TIMEOUT)
          else:
            #Message failed due to exceeded number of resent attempts
            if message_queue_itm.get_sender() == self.config.MY_ADDRESS:
              #Message was created by me, update state to failed or delete, if its W_ACK message set state to failed
              if message_queue_itm.get_message_type() != MessageType.TEXT_MSG_W_ACK:
                message_queue_itm.update_message_state(MessageState.DELETED)
                message_queue_itm.update_last_millis()
                message_queue_itm.set_timeout(self.config.DELETE_WAIT_TIME*1000)
                gc.collect()
                return
              else:
                #This is only for TEXT_MSG_W_ACK message, this means that message failed to be rebroadcasted by any other node
                message_queue_itm.update_message_state(MessageState.FAILED)
                self.notification_callback(f"Message {message_queue_itm.get_message_id()} failed to be sent")
            else:
              #Message was created by someone else, delete it from queue
              message_queue_itm.update_message_state(MessageState.DELETED)
              message_queue_itm.update_last_millis()
              message_queue_itm.set_timeout(self.config.DELETE_WAIT_TIME*1000)
      elif message_queue_itm.get_state() == MessageState.REBROADCASTED:
        if message_queue_itm.get_last_millis() + message_queue_itm.get_timeout() < round(time.monotonic() * 1000):
          #Message was rebroadcasted, but ACK was not received in time
          message_queue_itm.update_message_state(MessageState.NAK)
      elif message_queue_itm.get_state() == MessageState.DELETED:
        if message_queue_itm.get_last_millis() + message_queue_itm.get_timeout() < round(time.monotonic() * 1000):
          #Message delete timeout passed, delete message for real
          self.notification_callback(f"Deleting message {message_queue_itm.get_message_id()}")
          del self.message_queue[message_queue_itm.get_message_id()]
    gc.collect()

  def get_user_messages(self):
    messages = []
    for message_queue_itm in self.message_queue.values():
      if message_queue_itm.get_message_type() != MessageType.ACK and message_queue_itm.get_message_type() != MessageType.TRACEROUTE_REQUEST and message_queue_itm.get_state() != MessageState.DELETED:
        if message_queue_itm.get_sender() == self.config.MY_ADDRESS and message_queue_itm.get_message_type() != MessageType.TRACEROUTE:
          messages.append(message_queue_itm)
        elif message_queue_itm.get_destination() == self.config.MY_ADDRESS or (message_queue_itm.get_destination() == self.config.BROADCAST_ADDRESS and message_queue_itm.get_state() != MessageState.DONE):
          messages.append(message_queue_itm)
        elif message_queue_itm.get_message_type() == MessageType.RAW_PACKET and self.config.MONITORING_ENABLED:
          messages.append(message_queue_itm)
    return messages

  def get_message_queue(self):
    return self.message_queue

  def get_stats(self):
    return (self.received_counter, self.sent_counter)