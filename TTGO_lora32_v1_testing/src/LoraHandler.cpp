#include "main.h"

/*
  Bw125Cr45Sf128
  Bw500Cr45Sf128
  Bw31_25Cr48Sf512
  Bw125Cr48Sf4096
*/
uint16_t bandwidthOptions[4] = {125, 500, 31, 125};
uint8_t codingRateOptions[4] = {5, 5, 8, 8};
uint8_t spreadingFactorOptions[4] = {7, 7, 9, 12};

CTR<AES128> ctraes128;
byte key[16] = {0x53, 0x69, 0x78, 0x74, 0x65, 0x65, 0x6E, 0x20, 0x62, 0x79, 0x74, 0x65, 0x20, 0x6B, 0x65, 0x79}; //"Sixteen byte key"
Adafruit_SSD1306 *display_glob;
bool newMessage = false;
int newPacketSize = 0;

union twoByte
{
  uint16_t value;
  unsigned char Bytes[2];
} twoByteVal;

union fourByte
{
  uint32_t value;
  unsigned char Bytes[4];
} fourByteVal;

void initLoRa(Adafruit_SSD1306 &display)
{
  Serial.println("Initializing LoRa....");
  display_glob = &display;
  SPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_CS);
  LoRa.setPins(LORA_CS, LORA_RST, LORA_IRQ);

  int result = LoRa.begin(LORA_BAND);
  if (result != 1)
  {
    display.setCursor(0, 10);
    display.println("Failed to start LoRa network!");
    for (;;)
      ;
  }
  ctraes128.setKey(key, 16);
  ctraes128.setIV(key, 16);

  setSettings(DEFAULT_CONFIG);

  Serial.println("LoRa initialized");
  display.display();
  delay(500);
  display.setCursor(0, 15);
  display.println("LoRa network OK!");
  display.display();

  LoRa.onReceive(receiveMessage);
  LoRa.onTxDone(onTxDone);
  LoRa.receive();
}

void setSettings(uint8_t config){
  double bandwidth = bandwidthOptions[config] * 1000;
  LoRa.setSignalBandwidth(500E3);
  LoRa.setSpreadingFactor(spreadingFactorOptions[config]);
  LoRa.setCodingRate4(codingRateOptions[config]);

  //Default, do not change
  LoRa.setSyncWord(0x12);
  LoRa.setPreambleLength(8);
  LoRa.setGain(6);
}

void sendConfirmation(byte msgId3, byte msgId2, byte msgId1, byte msgId0)
{
  /* byte confirmationMsg[17] = {
      0x13,
      0x12,
      0x11,
      0x22, // Destination
      0x13,
      0x12,
      0x11,
      0x44, // Sender
      msgId3,
      msgId2,
      msgId1,
      msgId0,
      0,
      0,
      0,
      3,
      0x21 // Confirmation
  };
  LoRa.beginPacket();
  LoRa.write(confirmationMsg, 17);
  LoRa.endPacket(true); */
}

byte* createHeader(uint16_t destinationAddress, uint16_t senderAddress, uint8_t messageType, uint8_t priority){
  uint32_t messageId = (uint32_t)((random(200) / 100.0) * (uint32_t)random(LONG_MAX)); //TODO random returns signed long, but messageId is unsigned

  static byte header[10];
  twoByteVal.value = destinationAddress;
  header[0] = twoByteVal.Bytes[1];
  header[1] = twoByteVal.Bytes[0];

  twoByteVal.value = senderAddress;
  header[2] = twoByteVal.Bytes[1];
  header[3] = twoByteVal.Bytes[0];

  fourByteVal.value = messageId;
  header[4] = fourByteVal.Bytes[3];
  header[5] = fourByteVal.Bytes[2];
  header[6] = fourByteVal.Bytes[1];
  header[7] = fourByteVal.Bytes[0];

  header[8] = messageType;
  header[9] = priority;
  return header;
}

void sendTextMessage(String message, bool receiveAck, uint8_t maxHop, uint8_t priority)
{
  byte *header = createHeader(0xE67E, MY_ADDRESS, receiveAck ? 1 : 0, priority);

  byte messagePrefix[TEXTMESSAGE_PREFIX_LENGTH];
  fourByteVal.value = 1667116784; //TODO timestamp should go here
  messagePrefix[0] = fourByteVal.Bytes[3];
  messagePrefix[1] = fourByteVal.Bytes[2];
  messagePrefix[2] = fourByteVal.Bytes[1];
  messagePrefix[3] = fourByteVal.Bytes[0];
  messagePrefix[4] = maxHop;

  byte messageByteArr[message.length() + 1];
  message.getBytes(messageByteArr, message.length() + 1);

  /* byte encryptedMessage[message.length()]; //TODO encryption disabled for now, makes for easier debugging
  ctraes128.setKey(key, 16);
  ctraes128.setIV(key, 16);
  ctraes128.encrypt(encryptedMessage, messageByteArr, message.length());*/

  byte wholePayload[HEADER_LENGTH + TEXTMESSAGE_PREFIX_LENGTH + message.length()];
  memcpy(wholePayload, header, HEADER_LENGTH);
  memcpy(&wholePayload[HEADER_LENGTH], messagePrefix, TEXTMESSAGE_PREFIX_LENGTH);

  //memcpy(&wholePayload[sizeof(header)], encryptedMessage, sizeof(encryptedMessage));
  memcpy(&wholePayload[HEADER_LENGTH+TEXTMESSAGE_PREFIX_LENGTH], messageByteArr, message.length());

  Serial.println("Payload: ");
  for (int i = 0; i < HEADER_LENGTH + TEXTMESSAGE_PREFIX_LENGTH  + message.length(); i++)
  {
    Serial.print(wholePayload[i], HEX);
    if (i == HEADER_LENGTH - 1 || i == HEADER_LENGTH + TEXTMESSAGE_PREFIX_LENGTH - 1)
      Serial.print(" | ");
    else
      Serial.print(" ");
  }
  Serial.println();

  LoRa.beginPacket();
  LoRa.write(wholePayload, HEADER_LENGTH + TEXTMESSAGE_PREFIX_LENGTH + message.length());
  LoRa.endPacket(true);
}

void checkForMessage(){
  if (newMessage)
    processNewMessage();
}

void receiveMessage(int packetSize){
  newMessage  = true;
  newPacketSize = packetSize;
}

void processNewMessage(){
  if (newPacketSize)
  {
    newMessage = false;
    byte data[newPacketSize];

    int rssi = LoRa.packetRssi();
    int snr = LoRa.packetSnr();

    Serial.print("\nReceived packet: ");
    for (int i = 0; i < newPacketSize; i++)
    {
      byte c = LoRa.read();
      Serial.print(c, HEX);
      Serial.print(" ");
      data[i] = c;
    }
    Serial.println();

    //Check if destination address is my address or broadcast
    twoByte destination;
    destination.Bytes[1] = data[0];
    destination.Bytes[0] = data[1];

    if (destination.value != MY_ADDRESS && destination.value != BROADCAST_ADDRESS){
      return;
    }
    // TODO may break if random message with FF FF is received

    uint8_t messagePrefixLength;
    switch (data[8]){
      case 0:
      case 1:
        messagePrefixLength = TEXTMESSAGE_PREFIX_LENGTH;
        break;
      case 2:
        messagePrefixLength = SENSORMESSAGE_PREFIX_LENGTH;
        break;
      default:
        messagePrefixLength = TEXTMESSAGE_PREFIX_LENGTH;
        break;
    }

    uint32_t messageLength = newPacketSize - HEADER_LENGTH - messagePrefixLength;
    byte header[HEADER_LENGTH];
    byte messagePrefix[messagePrefixLength];
    byte message[messageLength];

    memcpy(header, data, HEADER_LENGTH);
    memcpy(messagePrefix, &data[HEADER_LENGTH], messagePrefixLength);
    memcpy(message, &data[HEADER_LENGTH + messagePrefixLength], messageLength);

    twoByte sender;
    sender.Bytes[1] = header[2];
    sender.Bytes[0] = header[3];

    fourByte messageId;
    messageId.Bytes[3] = header[4];
    messageId.Bytes[2] = header[5];
    messageId.Bytes[1] = header[6];
    messageId.Bytes[0] = header[7];

    /*
    byte messageDecrypted[messageLength];
    ctraes128.setKey(key, 16);
    ctraes128.setIV(key, 16);
    ctraes128.decrypt(messageDecrypted, message, messageLength);
    */
    String msg = "";
    Serial.print("Decrypted: ");
    for (int i = 0; i < messageLength; i++)
    {
      msg += (char)message[i];
      Serial.print(message[i], HEX);
      Serial.print(" ");
    }
    Serial.println();

    Serial.println("Received message:");
    Serial.println("| DESTINATION \t | SENDER \t | MESSAGE ID \t | MAX HOP \t | RSSI \t | SNR \t | MESSAGE \t |");
    Serial.println("##########################################################################################################");
    String outputStr = "| " + String(destination.value, HEX) + "\t\t | " + String(sender.value, HEX) + "\t\t | " + String(messageId.value, HEX) + "\t | " + String(message[4]) + "\t\t | " + String(rssi) + "\t\t | " + String(snr) + "\t | " + msg;
    Serial.println(outputStr);

    display_glob->clearDisplay();
    display_glob->setCursor(0, 2);
    display_glob->print("Received:");
    display_glob->setCursor(0, 12);
    display_glob->print(msg);
    display_glob->setCursor(0, 40);
    display_glob->print("RSSI:");
    display_glob->print(rssi);
    display_glob->setCursor(0, 50);
    display_glob->print("SNR:");
    display_glob->print(snr);
    display_glob->display();

    /*delay(700);
    sendConfirmation(data[8], data[9], data[10], data[11]);
    delay(200);
    if (msg == "Ping")
    {
      sendTextMessage("Pong");
    } */
    newPacketSize = 0;
  }
}

void onTxDone(){
  LoRa.receive();
}