#include <Crypto.h>
#include <AES.h>
#include <CTR.h>
#include <Array.h>


////////////////////////////////////////////////////////////////////////
//Config variables

#define MY_ADDRESS 0x0003
#define SEND_INTERVAL 120 //Seconds, how often to send data
#define AES_KEY "SuperTajne heslo" //Must be 16 characters long
#define LORA_BW 500
#define LORA_CR 6
#define LORA_SF 9
#define RESEND_COUNT 4 //How many times to resend single message
#define RESEND_TIMEOUT 5 //Seconds, how long to wait before resending
#define DEFAULT_TTL 120 //Seconds
static uint16_t CONTACTS[] = { 0x0005 }; //Node will be sending messages to these addresses
#define RANDOM_GPS //Uncomment to use random GPS coordinates when GPS cannot aquire fix. Otherwise it will send zeros as coordinates
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