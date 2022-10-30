#include <Crypto.h>
#include <AES.h>
#include <CTR.h>

#include "Message.h"


#define MY_ADDRESS 0xA02C
#define AES_KEY {0x53, 0x69, 0x78, 0x74, 0x65, 0x65, 0x6E, 0x20, 0x62, 0x79, 0x74, 0x65, 0x20, 0x6B, 0x65, 0x79} //"Sixteen byte key"
#define DEBUG 1

#define BROADCAST_ADDRESS 0xFFFF
#define HEADER_LENGTH 10
#define TEXTMESSAGE_PREFIX_LENGTH 5
#define SENSORMESSAGE_PREFIX_LENGTH 6

class MessageHandler {
  private:
    byte key[16];
    CTR<AES128> aes128;

  public:
    MessageHandler();
    byte* createTextMessage(uint16_t destinationAddress, uint32_t& byteArraySize, String message, bool receiveAck=false, uint8_t maxHop=5, uint8_t priority=0);
    Message* processNewMessage(byte* message, uint32_t newPacketSize, float rssi, float snr);
    byte* createHeader(uint16_t destinationAddress, uint16_t senderAddress, uint8_t messageType, uint8_t priority = 0);
};
