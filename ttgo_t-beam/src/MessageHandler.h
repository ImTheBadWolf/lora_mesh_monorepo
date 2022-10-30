#include "Message.h"

class MessageHandler {
  private:
    byte key[16];

  public:
    MessageHandler();
    byte* createTextMessage(uint32_t& byteArraySize, String message, bool receiveAck=false, uint8_t maxHop=5, uint8_t priority=0);
    Message* processNewMessage(byte* message, uint32_t newPacketSize, float rssi, float snr);
    byte* createHeader(uint16_t destinationAddress, uint16_t senderAddress, uint8_t messageType, uint8_t priority = 0);
};
