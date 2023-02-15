#include "MessageHandler.h"

union twoByte
{
  uint16_t value;
  unsigned char Bytes[2];
} twoByteVal;

union fourByte
{
  uint32_t value;
  unsigned char Bytes[4];
} fourByteVal;

MessageHandler::MessageHandler()
{
  CTR<AES128> ctraes128 = CTR<AES128>();
  this->generateAesKey();
  Array<QueueMessage *, MESSAGE_QUEUE_SIZE> messageQueue;
};

void MessageHandler::generateAesKey()
{
  String keyStr = AES_KEY;
  if (keyStr.length() != 16)
  {
    while (true)
    {
      Serial.println("AES_KEY must be 16 characters long"); // TODO console displays some weird characters instead of this... Serial is not initialised yet
      delay(2000);
    }
  }

  keyStr.getBytes(this->key, 16 + 1);
}

byte *MessageHandler::createHeader(uint16_t destinationAddress, uint16_t senderAddress, uint8_t messageType, uint8_t priority)
{
  uint32_t messageId = (uint32_t)((random(200) / 100.0) * (uint32_t)random(LONG_MAX)); // TODO random returns signed long, but messageId is unsigned

  static byte header[10];
  twoByteVal.value = destinationAddress;
  header[0] = twoByteVal.Bytes[1];
  header[1] = twoByteVal.Bytes[0];

  twoByteVal.value = senderAddress;
  header[2] = twoByteVal.Bytes[1];
  header[3] = twoByteVal.Bytes[0];

  fourByteVal.value = messageId;
  header[4] = fourByteVal.Bytes[3];
  header[5] = fourByteVal.Bytes[2];
  header[6] = fourByteVal.Bytes[1];
  header[7] = fourByteVal.Bytes[0];

  twoByte checksum;
  checksum.value = this->calculateChecksum(header);
  header[8] = checksum.Bytes[1];
  header[9] = checksum.Bytes[0];

  header[10] = messageType;
  header[11] = priority;
  return header;
}

uint16_t MessageHandler::calculateChecksum(byte *data)
{
  // Calculates CRC-CCITT checksum of first 8 bytes of data
  uint8_t length = 8;
  unsigned char x;
  unsigned short crc = 0xFFFF;

  while (length--)
  {
    x = crc >> 8 ^ *data++;
    x ^= x >> 4;
    crc = (crc << 8) ^ ((unsigned short)(x << 12)) ^ ((unsigned short)(x << 5)) ^ ((unsigned short)x);
  }
  return crc;
}

byte *MessageHandler::createTextMessage(uint16_t destinationAddress, uint32_t &byteArraySize, String message, bool receiveAck, uint8_t maxHop, uint8_t priority)
{
  byte *header = createHeader(destinationAddress, MY_ADDRESS, receiveAck ? 1 : 0, priority);

  byte messagePrefix[TEXTMESSAGE_PREFIX_LENGTH]; //TODO timestamp is removed, text message prefix contains only maxhop, sensor message contains TTL, ping message contains ping type
  messagePrefix[1] = maxHop; //TODO for sensor data this is ttl

  byte messageByteArr[message.length() + 1];
  message.getBytes(messageByteArr, message.length() + 1);

  byte encryptedMessage[message.length()];

  this->ctraes128.setKey(this->key, 16);
  this->ctraes128.setIV(this->key, 16);
  this->ctraes128.encrypt(encryptedMessage, messageByteArr, message.length());

  byte *wholePayload = new byte[HEADER_LENGTH + TEXTMESSAGE_PREFIX_LENGTH + message.length()];
  memcpy(wholePayload, header, HEADER_LENGTH);
  memcpy(&wholePayload[HEADER_LENGTH], messagePrefix, TEXTMESSAGE_PREFIX_LENGTH);

  // TODO if crypto disabled, this option will not be available
  // memcpy(&wholePayload[HEADER_LENGTH+TEXTMESSAGE_PREFIX_LENGTH], messageByteArr, message.length());
  memcpy(&wholePayload[HEADER_LENGTH + TEXTMESSAGE_PREFIX_LENGTH], encryptedMessage, message.length());

  if (DEBUG)
  {
    Serial.println("Payload: ");
    for (int i = 0; i < HEADER_LENGTH + TEXTMESSAGE_PREFIX_LENGTH + message.length(); i++)
    {
      Serial.print(wholePayload[i], HEX);
      if (i == HEADER_LENGTH - 1 || i == HEADER_LENGTH + TEXTMESSAGE_PREFIX_LENGTH - 1)
        Serial.print(" | ");
      else
        Serial.print(" ");
    }
    Serial.println();
  }
  byteArraySize = HEADER_LENGTH + TEXTMESSAGE_PREFIX_LENGTH + message.length();
  return wholePayload;
}

Message *MessageHandler::processNewMessage(byte *message, uint32_t newPacketSize, float rssi, float snr)
{
  if (newPacketSize)
  {
    byte data[newPacketSize];
    if (DEBUG)
    {
      Serial.print("\nReceived packet: ");
      for (int i = 0; i < newPacketSize; i++)
      {
        Serial.print(message[i], HEX);
        data[i] = message[i];
        Serial.print(" ");
      }
      Serial.println();
    }

    uint16_t checksum = calculateChecksum(data);
    twoByte receivedChecksum;
    receivedChecksum.Bytes[1] = data[8];
    receivedChecksum.Bytes[0] = data[9];

    if (checksum == receivedChecksum.value){
      // Check if destination address is my address or broadcast
      twoByte destination;
      destination.Bytes[1] = data[0];
      destination.Bytes[0] = data[1];
      if (destination.value == MY_ADDRESS || destination.value == BROADCAST_ADDRESS || MONITORING)
      {
        uint8_t messagePrefixLength;
        switch (data[10])
        {
        case 0:
        case 1:
          messagePrefixLength = TEXTMESSAGE_PREFIX_LENGTH;
          break;
        case 2:
          messagePrefixLength = SENSORMESSAGE_PREFIX_LENGTH;
          break;
        default:
          messagePrefixLength = TEXTMESSAGE_PREFIX_LENGTH;
          break;
        }

        uint32_t messageLength = newPacketSize - HEADER_LENGTH - messagePrefixLength;
        byte header[HEADER_LENGTH];
        byte messagePrefix[messagePrefixLength];
        byte message[messageLength];
        memcpy(header, data, HEADER_LENGTH);
        memcpy(messagePrefix, &data[HEADER_LENGTH], messagePrefixLength);
        memcpy(message, &data[HEADER_LENGTH + messagePrefixLength], messageLength);

        twoByte sender;
        sender.Bytes[1] = header[2];
        sender.Bytes[0] = header[3];

        fourByte messageId;
        messageId.Bytes[3] = header[4];
        messageId.Bytes[2] = header[5];
        messageId.Bytes[1] = header[6];
        messageId.Bytes[0] = header[7];

        byte messageDecrypted[messageLength];
        this->ctraes128.setKey(this->key, 16);
        this->ctraes128.setIV(this->key, 16);
        this->ctraes128.decrypt(messageDecrypted, message, messageLength);

        Message *receivedMessage = new Message(destination.value, sender.value, messageId.value, header[10], header[11], messagePrefix[0], messageDecrypted, messageLength, rssi, snr);

        if (DEBUG)
        {
          Serial.print("Decrypted: ");
          for (int i = 0; i < messageLength; i++)
          {
            Serial.print(messageDecrypted[i], HEX);
            Serial.print(" ");
          }
          Serial.println();
          /*
          Serial.println("Received message:");
          Serial.println("| DESTINATION \t | SENDER \t | MESSAGE ID \t | MAX HOP \t | RSSI \t | SNR \t | MESSAGE \t |");
          Serial.println("##########################################################################################################");
          Serial.println(receivedMessage->toString()); */
        }
        /*TODO if msg type = 1, send ACK of received message
        sendConfirmation(data[8], data[9], data[10], data[11]);*/

        return receivedMessage;
      }
      else
      {
        // TODO if message is not for me and checksum matches, add it to rebroadcast queue
        // Validation is needed before, to not queue messages that are not part of this protocol
      }
    }
    else {
      Serial.println("Checksum does not match");
      Serial.println("Received checksum: " + String(receivedChecksum.value));
      Serial.println("Calculated checksum: " + String(checksum));
    }
  }
  return new Message();
}