#include <Crypto.h>
#include <AES.h>
#include <CTR.h>
#include <Array.h>


////////////////////////////////////////////////////////////////////////
//Config variables

#define MY_ADDRESS 0xC2F1
#define SEND_INTERVAL 90 //Seconds, how often to send data
#define AES_KEY "SuperTajne heslo" //Must be 16 characters long
#define LORA_BW 500
#define LORA_CR 6
#define LORA_SF 9
#define RESEND_COUNT 5 //How many times to resend single message
#define RESEND_TIMEOUT 8 //Seconds, how long to wait before resending
#define DEFAULT_TTL 120 //Seconds
static uint16_t CONTACTS[] = { 0xFFFF, 0xA1BC, 0x0002 };
#define BROADCAST_ADDRESS 0xFFFF
//End of config variables
////////////////////////////////////////////////////////////////////////

class MessageHandler {
  private:
    byte key[17];
    CTR<AES128> ctraes128;
    void generateAesKey();
    uint16_t calculateChecksum(byte* data);

  public:
    MessageHandler();
    byte* createSensorMessage(uint16_t destinationAddress, uint32_t& byteArraySize, String message, uint16_t ttlIn = DEFAULT_TTL);
    byte* createHeader(uint16_t destinationAddress, uint16_t senderAddress);
};

class QueueItem {
  private:
    uint32_t timeout;
    uint8_t resendCounter;
    byte* payloadBytes;
    uint8_t payloadBytesSize;
  public:
    QueueItem(uint32_t timeout_i, uint8_t resendCounter_i, byte *payloadBytes_i, uint8_t payloadBytesSize_i);
    uint32_t getTimeout();
    uint8_t getResendCounter();
    byte* getPayloadBytes();
    uint8_t getPayloadBytesSize();
    void setTimeout(uint32_t timeout_i);
    void decrementResendCounter();
};

#define HEADER_LENGTH 12