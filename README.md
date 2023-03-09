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
  * 0 - text message
  * 1 - text message with ACK, reffered to as `W_ACK`
  * 2 - sensor data
  * 255 - ACK confirmation message

---

## Payload packets

### Text message /Text message with ACK packet

| 1B | 0 - 241B |
|----|----|
|Max hop|Message|

### Sensor data packet

| 2B | 0 - 240B |
|----|----|
|TTL|data|

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
* ACK_WAIT_TIME - how long to wait for ACK message until message is considered as failed(NAK)

---
## State flow

![State flow](state_flow.png)
