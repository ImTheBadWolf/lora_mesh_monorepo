# LoRa Mesh protocol


## Message header
| 2B | 2B | 4B | 2B | 1B | 1B | 0 - 242B |
|----|----|----|----|----|----|----|
|Destination address|Sender address|Message ID|Checksum|Message Type|Priority|Payload|

* Destination address - 0xFFFF reserved for broadcast
* Message ID - random unsigned int, used also in `message queue`
* Checksum - CRC-16/CCITT-FALSE, checksum of destination, sender and message ID. Used to identify messages belonging to this protocol
* Priority - overrides the order in `message queue`
* Message type
  * 0 - ACK confirmation message (Payload not encrypted)
  * 1 - text message
  * 2 - text message with ACK, reffered to as `W_ACK`
  * 3 - sensor data
  * 4 - traceroute request (Payload is empty)
  * 5 - traceroute (Payload not encrypted)

---

## Payload packets

### Text message/Text message with ACK confirmation

| 1B | 1B | 0 - 240B |
|----|----|----|
|Max hop|Initial Max hop|Message|

### Sensor data packet

| 2B | 0 - 240B |
|----|----|
|TTL|data|

### Traceroute request packet

| 1B | 1B |
|----|----|
|Max hop|Initial Max hop|

### Traceroute packet

| 1B | 0 - 240B |
|----|----|
|Max hop|Route path|

### ACK message packet

| 1B | 4B |
|----|----|
|Max hop|Message ID|

* Message ID - ID of the message this ACK is confirming

---

## Message state

* NEW - newly created message
* SENT - message after it was sent for the first time
* REBROADCASTED - used only with `W_ACK` messages, this state is used to wait for ACK confirmation
* ACK - used only with `W_ACK` messages, message has been ACK-ed
* DONE - non `W_ACK` message has been rebroadcasted by at least one other node
* NAK - `W_ACK` message has not been ACK-ed after timeout runs out
* FAILED - message has been sent maximum amount of times(`RESEND_COUNT`) without any other node rebroadcasting it

---

## Configuration variables

* RESEND_COUNT - how many times should the message be resent until considered as failed
* RESEND_TIMEOUT - how long to wait before the message is resent (In seconds)
* ACK_WAIT_TIME - how long to wait (In seconds) for ACK message until message is considered as failed(NAK)
* RANDOMIZE_PATH - experimental setting, When enabled it will randomize rebroadcast timeouts (timeout wont be based on SNR). This can help deliver messages that could not be delivered because of not optimal network topology

---

## API

```
MESSAGE_ENTITY = {
  'id': Number, //Message ID
  'from': String, //Sender, hex address is translated (on FE) to contact name if it exists
  'to': String, //Destination, hex address is translated (on FE) to contact name if it exists
  'payload': String
  'msg_type': OneOf('TEXT', 'WACK_TEXT', 'SENSOR', 'TRACEROUTE'),
  'my_msg': Bool, //Optional, set only for users own messages
  'state': OneOf('DONE', 'REBROADCASTED', 'ACK', 'NAK', 'FAILED',), //Set only on received messages
}
```
```
NEW_MESSAGE_ENTITY = {
  'destination': Number, //Hex address
  'message': String, //Max 240B
  'max_hop': Number, //0-255
  'priority': Number, //0(Normal priority) or 1(High priority)
  'wack': Bool //Flag if ACK should be received for that message
}
```

## /api/messages [GET]

Returns list of messages.
```
data = {
  'messages': [MESSAGE_ENTITY...]
}
```

## /api/send_text_message [POST]

Create and send new message (text messages only).  
Input: NEW_MESSAGE_ENTITY

## /api/traceroute [POST]

Create and send traceroute request.  
Traceroute response will arrive later and be loaded with `/api/messages`  
Input:
```
TRACEROUTE_REQUEST = {
  'destination': Number, //Hex address
  'max_hop': Number, //0-255
  'priority': Number, //0(Normal priority) or 1(High priority)
}
```

## /api/contacts [GET]

Returns list of contacts
```
CONTACT_ENTITY = {
  'addres': Number, //Hex address
  'name': String, //Contact name, max 25 chars
}
```

## /api/contact [PUT]

Create new contact  
Input: `CONTACT_ENTITY`

## /api/contact [DELETE]

Delete contact  
Input: contact addres

## /api/sensors [GET]

Returns list of sensors

```
SENSOR_ENTITY = {
  'addres': Number, //Hex address
  'name': String, //Sensor name, max 25 chars
}
```

## /api/sensor [PUT]

Create new sensor  
Input: `SENSOR_ENTITY`

## /api/sensor [DELETE]

Delete sensor  
Input: sensor addres

## TODO config api

* list all config variables
* list saved wifi networs (preferably without passwords ?)
* set device address => Until the address is set, everything else should be disabled. Home page, sensor, contacts page should redirect to config and display alert about mandatory address setting. Address can be changed only once.
* set other config variables
* add wifi network
* remove wifi network

## TODO other processing apis
This APIs wont be used in webGUI but can be usefull for further development and debugging/testing
* create sensor message api
* dump messageQueue - this will return all the messages that are currently in messageQueue, with all the usefull information about each message like timeouts, maxhop/ttl etc...



---

## State flow

![State flow](state_flow.png)
