#define DEFAULT_CONFIG 1 //Default Bw500Cr45Sf128


void initLoRa(Adafruit_SSD1306 &display);
void setSettings(uint8_t config);
void sendConfirmation(byte msgId3, byte msgId2, byte msgId1, byte msgId0);
void sendTextMessage(String message, bool receiveAck=false, uint8_t maxHop=5, uint8_t priority=0);
void receiveMessage(int packetSize);
void checkForMessage();
//void processNewMessage();
void processNewMessage();
void onTxDone();
byte* createHeader(uint16_t destinationAddress, uint16_t senderAddress, uint8_t messageType, uint8_t priority = 0);