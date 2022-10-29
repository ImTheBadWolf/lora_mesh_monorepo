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
  byte confirmationMsg[17] = {
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
  LoRa.endPacket(true);
}

void sendMessage(String message)
{
  byte messageByteArr[message.length() + 1];
  message.getBytes(messageByteArr, message.length() + 1);

  byte header[16] = {
      0x13,
      0x12,
      0x11,
      0x22, // Destination
      0x13,
      0x12,
      0x11,
      0x44, // Sender
      0x13,
      0x12,
      (byte)random(255),
      (byte)random(255),
      0,
      0,
      0,
      3};
  byte input[message.length() + 7];
  byte output[message.length() + 7];

  for (int i = 0; i < message.length(); i++)
  {
    input[i] = messageByteArr[i];
  }
  for (int i = message.length(); i < message.length() + 7; i++)
  {
    input[i] = 0x7C;
  }

  ctraes128.setKey(key, 16);
  ctraes128.setIV(key, 16);
  ctraes128.encrypt(output, input, message.length() + 7);
  byte outputMessage[16 + message.length() + 7];
  memcpy(outputMessage, header, sizeof(header));
  memcpy(&outputMessage[sizeof(header)], output, sizeof(output));

  LoRa.beginPacket();
  LoRa.write(outputMessage, 16 + message.length() + 7);
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
    Serial.print("Received packet: ");
    String msg = "";
    int data[newPacketSize];

    int rssi = LoRa.packetRssi();
    int snr = LoRa.packetSnr();

    for (int i = 0; i < newPacketSize; i++)
    {
      int c = LoRa.read();
      Serial.print(c, HEX);
      Serial.print(" ");
      data[i] = c;
    }

    Serial.println();
    if (data[16] == 33 || data[3] != 0x22)
    { // Symbol "!" for delivery confirmation
      return;
    }

    byte strippedData[newPacketSize - 16];
    byte output[newPacketSize - 16];
    for (int i = 0; i < newPacketSize - 16; i++)
    {
      strippedData[i] = data[16 + i];
    }
    ctraes128.setKey(key, 16);
    ctraes128.setIV(key, 16);
    ctraes128.decrypt(output, strippedData, newPacketSize - 16);
    Serial.print("Decrypted: ");
    for (int i = 0; i < newPacketSize - 16; i++)
    {
      if (output[i] != 0x7C)
        msg += (char)output[i];
      Serial.print(output[i], HEX);
      Serial.print(" ");
    }
    Serial.println();
    Serial.println(msg);

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

    delay(700);
    sendConfirmation(data[8], data[9], data[10], data[11]);
    delay(200);
    if (msg == "Ping")
    {
      sendMessage("Pong");
    }
    newPacketSize = 0;
  }
}

void onTxDone(){
  LoRa.receive();
}