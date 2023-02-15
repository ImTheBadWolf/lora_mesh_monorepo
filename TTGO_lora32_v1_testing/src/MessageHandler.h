#include <Crypto.h>
#include <AES.h>
#include <CTR.h>
#include <Array.h>

#include "Message.h"
#include "QueueMessage.h"


#define MY_ADDRESS 0x0004
#define AES_KEY "SuperTajne heslo" //Must be 16 characters long
#define DEBUG 1
#define MONITORING 0
#define MESSAGE_QUEUE_SIZE 20

#define BROADCAST_ADDRESS 0xFFFF
#define HEADER_LENGTH 12
#define TEXTMESSAGE_PREFIX_LENGTH 1
#define SENSORMESSAGE_PREFIX_LENGTH 6

class MessageHandler {
  private:
    byte key[17];
    CTR<AES128> ctraes128;
    Array<QueueMessage*, MESSAGE_QUEUE_SIZE> messageQueue;
    void generateAesKey();
    uint16_t calculateChecksum(byte* data);

  public:
    MessageHandler();
    byte* createTextMessage(uint16_t destinationAddress, uint32_t& byteArraySize, String message, bool receiveAck=false, uint8_t maxHop=5, uint8_t priority=0);
    Message* processNewMessage(byte* message, uint32_t newPacketSize, float rssi, float snr);
    byte* createHeader(uint16_t destinationAddress, uint16_t senderAddress, uint8_t messageType, uint8_t priority = 0);
};
