#include <Arduino.h>

class Message {
  private:
    uint16_t destinationAddress;
    uint16_t senderAddress;
    uint32_t messageID;
    uint8_t messageType;
    uint8_t priority;
    //uint32_t timestamp; TODO
    uint8_t maxHop;
    byte* payload;
    uint32_t payloadSize;
    float rssi;
    float snr;
    String strMsg;
    String getStringFromMessage(byte* payload, uint32_t payloadSize);
    bool valid;

  public:
    Message();
    Message(uint16_t destinationAddress, uint16_t senderAddress, uint32_t messageID, uint8_t messageType, uint8_t priority, uint8_t maxHop, byte* payload, uint32_t payloadSize, float rssi, float snr);
    ~Message();
    String toString();
    uint16_t getSenderAddress();
    String getMessage();
    bool isValid();
};