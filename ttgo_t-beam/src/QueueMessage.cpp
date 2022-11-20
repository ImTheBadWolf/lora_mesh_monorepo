#include "QueueMessage.h"

/*
byte* payload
    bool hasMaxHop;
    uint8_t maxHop;
    uint16_t ttl;
    uint8_t priority;
    uint32_t messageID;*/

QueueMessage::QueueMessage(byte *payload, uint8_t priority, uint32_t messageID, uint8_t maxHop, uint16_t ttl)
{
  this->payload = payload;
  if (maxHop && !ttl)
    this->hasMaxHop = true;
  this->ttl = ttl;
  this->maxHop = maxHop;
  this->priority = priority;
  this->messageID = messageID;
}

uint8_t QueueMessage::getPriority(){
  return this->priority;
}