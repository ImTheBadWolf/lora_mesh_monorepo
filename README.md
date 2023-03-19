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
  * 0 - ACK confirmation message
  * 1 - text message
  * 2 - text message with ACK, reffered to as `W_ACK`
  * 3 - sensor data
  * 4 - traceroute request
  * 5 - traceroute

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
## State flow

![State flow](state_flow.png)
