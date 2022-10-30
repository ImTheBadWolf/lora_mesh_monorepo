#include <Crypto.h>
#include <AES.h>
#include <CTR.h>

#include "Message.h"


#define MY_ADDRESS 0xE67E
#define AES_KEY "SuperTajne heslo" //Must be 16 characters long
#define DEBUG 1

#define BROADCAST_ADDRESS 0xFFFF
#define HEADER_LENGTH 10
#define TEXTMESSAGE_PREFIX_LENGTH 5
#define SENSORMESSAGE_PREFIX_LENGTH 6

class MessageHandler {
  private:
    byte key[17];
    CTR<AES128> ctraes128;
    void generateAesKey();

  public:
    MessageHandler();
    byte* createTextMessage(uint16_t destinationAddress, uint32_t& byteArraySize, String message, bool receiveAck=false, uint8_t maxHop=5, uint8_t priority=0);
    Message* processNewMessage(byte* message, uint32_t newPacketSize, float rssi, float snr);
    byte* createHeader(uint16_t destinationAddress, uint16_t senderAddress, uint8_t messageType, uint8_t priority = 0);
};
