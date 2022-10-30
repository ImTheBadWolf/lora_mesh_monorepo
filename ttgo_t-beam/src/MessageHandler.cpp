#include "main.h"


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

MessageHandler::MessageHandler(){
  byte key[16] = AES_KEY;
  // CTR<AES128> ctraes128;
};

byte* MessageHandler::createHeader(uint16_t destinationAddress, uint16_t senderAddress, uint8_t messageType, uint8_t priority){
  uint32_t messageId = (uint32_t)((random(200) / 100.0) * (uint32_t)random(LONG_MAX)); //TODO random returns signed long, but messageId is unsigned

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

  header[8] = messageType;
  header[9] = priority;
  return header;
}

byte* MessageHandler::createTextMessage(uint32_t &byteArraySize, String message, bool receiveAck, uint8_t maxHop, uint8_t priority){
  byte *header = createHeader(0xA02C, MY_ADDRESS, receiveAck ? 1 : 0, priority);//TODO destination address hardcoded for now

  byte messagePrefix[TEXTMESSAGE_PREFIX_LENGTH];
  fourByteVal.value = 1667116784; //TODO timestamp should go here, ttgo doesnt have rtc
  messagePrefix[0] = fourByteVal.Bytes[3];
  messagePrefix[1] = fourByteVal.Bytes[2];
  messagePrefix[2] = fourByteVal.Bytes[1];
  messagePrefix[3] = fourByteVal.Bytes[0];
  messagePrefix[4] = maxHop;

  byte messageByteArr[message.length() + 1];
  message.getBytes(messageByteArr, message.length() + 1);

  /* byte encryptedMessage[message.length()]; //TODO encryption disabled for now, makes for easier debugging
  ctraes128.setKey(key, 16);
  ctraes128.setIV(key, 16);
  ctraes128.encrypt(encryptedMessage, messageByteArr, message.length());*/

  byte* wholePayload = new byte[HEADER_LENGTH + TEXTMESSAGE_PREFIX_LENGTH + message.length()];
  memcpy(wholePayload, header, HEADER_LENGTH);
  memcpy(&wholePayload[HEADER_LENGTH], messagePrefix, TEXTMESSAGE_PREFIX_LENGTH);

  //memcpy(&wholePayload[sizeof(header)], encryptedMessage, sizeof(encryptedMessage));
  memcpy(&wholePayload[HEADER_LENGTH+TEXTMESSAGE_PREFIX_LENGTH], messageByteArr, message.length());

  if (DEBUG){
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

Message* MessageHandler::processNewMessage(byte *message, uint32_t newPacketSize, float rssi, float snr){
  if (newPacketSize)
  {
    byte data[newPacketSize + 1];
    if (DEBUG){
      Serial.print("\nReceived packet: ");
      for (int i = 0; i < newPacketSize; i++)
      {
        Serial.print(message[i], HEX);
        data[i] = message[i];
        Serial.print(" ");
      }
      Serial.println();
    }

    //Check if destination address is my address or broadcast
    twoByte destination;
    destination.Bytes[1] = data[0];
    destination.Bytes[0] = data[1];

    if (destination.value == MY_ADDRESS || destination.value == BROADCAST_ADDRESS){
      // TODO may break if random message with FF FF is received

      uint8_t messagePrefixLength;
      switch (data[8])
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

      Message *receivedMessage = new Message(destination.value, sender.value, messageId.value, header[8], header[9], messagePrefix[4], message, messageLength, rssi, snr);

      /*
      byte messageDecrypted[messageLength];
      ctraes128.setKey(key, 16);
      ctraes128.setIV(key, 16);
      ctraes128.decrypt(messageDecrypted, message, messageLength);
      */
      if (DEBUG)
      {
        String msg = "";
        Serial.print("Decrypted: ");
        for (int i = 0; i < messageLength; i++)
        {
          msg += (char)message[i];
          Serial.print(message[i], HEX);
          Serial.print(" ");
        }
        Serial.println();
/* 
        Serial.println("Received message:");
        Serial.println("| DESTINATION \t | SENDER \t | MESSAGE ID \t | MAX HOP \t | RSSI \t | SNR \t | MESSAGE \t |");
        Serial.println("##########################################################################################################");
        Serial.println(receivedMessage->toString()); */
      }
      /*delay(700);
      sendConfirmation(data[8], data[9], data[10], data[11]);
      delay(200);
      if (msg == "Ping")
      {
        sendTextMessage("Pong");
      } */
      return receivedMessage;
    }
  }
}