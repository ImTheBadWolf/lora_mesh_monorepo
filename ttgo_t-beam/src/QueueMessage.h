/*
  Class for managing messages in rebroadcasting queue
  MessageQueue should work like queue but messages should be accessible by theri messageID
*/
#include <Arduino.h>

class QueueMessage {
  private:
    byte* payload;
    bool hasMaxHop;
    uint8_t maxHop;
    uint16_t ttl;
    uint8_t priority;
    uint32_t messageID;
  public:
    void decrementTTL();
    void decrementMaxHop();
    QueueMessage(byte* payload, uint8_t priority, uint32_t messageID, uint8_t maxHop=0, uint16_t ttl=0);
    uint8_t getPriority();
};