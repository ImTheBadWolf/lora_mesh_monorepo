#define DEFAULT_CONFIG 1 //Default Bw500Cr45Sf128

void initLoRa(Adafruit_SSD1306 &display);
void setSettings(uint8_t config);
void sendConfirmation(byte msgId3, byte msgId2, byte msgId1, byte msgId0);
void sendMessage(String message);
void receiveMessage(int packetSize);
void checkForMessage();
void processNewMessage();
void onTxDone();