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
};

void MessageHandler::generateAesKey()
{
  String keyStr = AES_KEY;
  keyStr.getBytes(this->key, 16 + 1);
}

byte *MessageHandler::createHeader(uint16_t destinationAddress, uint16_t senderAddress)
{
  uint32_t messageId = (uint32_t)((random(200) / 100.0) * (uint32_t)random(LONG_MAX));

  static byte header[10];

  twoByte destinationAddress2b;
  destinationAddress2b.value = destinationAddress;
  header[0] = destinationAddress2b.Bytes[1];
  header[1] = destinationAddress2b.Bytes[0];

  twoByte senderAddress2b;
  senderAddress2b.value = senderAddress;
  header[2] = senderAddress2b.Bytes[1];
  header[3] = senderAddress2b.Bytes[0];

  fourByte messageId4b;
  messageId4b.value = messageId;
  header[4] = messageId4b.Bytes[3];
  header[5] = messageId4b.Bytes[2];
  header[6] = messageId4b.Bytes[1];
  header[7] = messageId4b.Bytes[0];

  twoByte checksum;
  checksum.value = this->calculateChecksum(header);
  header[8] = checksum.Bytes[1];
  header[9] = checksum.Bytes[0];

  header[10] = 3; //Message type always 3 => sensor_data
  header[11] = 0; //Priority always 0 => normal
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

byte *MessageHandler::createSensorMessage(uint16_t destinationAddress, uint32_t &byteArraySize, String message, uint16_t ttlIn)
{
  const uint8_t SENSOR_DATA_PREFIX_LENGTH = 2;  // Sensor_data has 2 byte TTL
  byte *header = createHeader(destinationAddress, MY_ADDRESS);

  byte messagePrefix[SENSOR_DATA_PREFIX_LENGTH];
  twoByte ttl;
  ttl.value = ttlIn;
  messagePrefix[0] = ttl.Bytes[1];
  messagePrefix[1] = ttl.Bytes[0];

  byte messageByteArr[message.length() + 1];
  message.getBytes(messageByteArr, message.length() + 1);

  byte encryptedMessage[message.length()];

  this->ctraes128.setKey(this->key, 16);
  this->ctraes128.setIV(this->key, 16);
  this->ctraes128.encrypt(encryptedMessage, messageByteArr, message.length());

  byte *wholePayload = new byte[HEADER_LENGTH + SENSOR_DATA_PREFIX_LENGTH + message.length()];
  memcpy(wholePayload, header, HEADER_LENGTH);
  memcpy(&wholePayload[HEADER_LENGTH], messagePrefix, SENSOR_DATA_PREFIX_LENGTH);

  if (destinationAddress != BROADCAST_ADDRESS)
    memcpy(&wholePayload[HEADER_LENGTH + SENSOR_DATA_PREFIX_LENGTH], encryptedMessage, message.length());
  else
    memcpy(&wholePayload[HEADER_LENGTH + SENSOR_DATA_PREFIX_LENGTH], messageByteArr, message.length());
  byteArraySize = HEADER_LENGTH + SENSOR_DATA_PREFIX_LENGTH + message.length();
  return wholePayload;
}

QueueItem::QueueItem(uint32_t timeout_i, uint8_t resendCounter_i, byte *payloadBytes_i, uint8_t payloadBytesSize_i)
{
  this->timeout = timeout_i;
  this->resendCounter = resendCounter_i;
  this->payloadBytes= payloadBytes_i;
  this->payloadBytesSize = payloadBytesSize_i;
};
uint32_t QueueItem::getTimeout()
{
  return this->timeout;
}
uint8_t QueueItem::getResendCounter()
{
  return this->resendCounter;
}
byte* QueueItem::getPayloadBytes()
{
  return this->payloadBytes;
}
uint8_t QueueItem::getPayloadBytesSize()
{
  return this->payloadBytesSize;
}
void QueueItem::setTimeout(uint32_t timeout_i)
{
  this->timeout = timeout_i;
}
void QueueItem::decrementResendCounter()
{
  this->resendCounter -= 1;
}