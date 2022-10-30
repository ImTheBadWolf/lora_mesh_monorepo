#include "main.h"

Message::Message(uint16_t destinationAddress, uint16_t senderAddress, uint32_t messageID, uint8_t messageType, uint8_t priority, uint8_t maxHop, byte *payload, uint32_t payloadSize, float rssi, float snr){
  this->destinationAddress = destinationAddress;
  this->senderAddress = senderAddress;
  this->messageID = messageID;
  this->messageType = messageType;
  this->priority = priority;
  this->maxHop = maxHop;
  this->payload = payload;
  this->payloadSize = payloadSize;
  this->rssi = rssi;
  this->snr = snr;
  this->strMsg = this->getStringFromMessage(this->payload, this->payloadSize);
}

Message::~Message(){}

String Message::getStringFromMessage(byte *payload, uint32_t payloadSize){
  String msg = "";
  for (int i = 0; i < payloadSize; i++)
  {
    msg += (char)payload[i];
  }
  return msg;
}

String Message::toString()
{
  return "| " + String(this->destinationAddress, HEX) + "\t\t | " + String(this->senderAddress, HEX) + "\t\t | " + String(this->messageID, HEX) + "\t | " + String(this->maxHop) + "\t\t | " + String(this->rssi) + "\t | " + String(this->snr) + "\t | " + this->strMsg;
}

uint16_t Message::getSenderAddress(){
  return this->senderAddress;
}