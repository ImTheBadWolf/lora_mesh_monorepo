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

bool buttonFlag = false;
bool newMessage = false;
int newPacketSize = 0;

Adafruit_SSD1306 display(128, 64, &Wire, OLED_RST);
MessageHandler messageHandler = MessageHandler();

void resetDisplay()
{
  digitalWrite(OLED_RST, LOW);
  delay(25);
  digitalWrite(OLED_RST, HIGH);
}
void initializeDisplay()
{
  Wire.begin(OLED_SDA, OLED_SCL);
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3c))
  {
    Serial.println("Failed to initialize the display");
    for (;;)
      ;
  }
  display.clearDisplay();

  display.setTextColor(WHITE);
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.println("Welcome to LORA");
  display.display();
}

void setSettings(uint8_t config)
{
  double bandwidth = bandwidthOptions[config] * 1000;
  LoRa.setSignalBandwidth(500E3);
  LoRa.setSpreadingFactor(spreadingFactorOptions[config]);
  LoRa.setCodingRate4(codingRateOptions[config]);

  // Default, do not change
  LoRa.setSyncWord(0x12);
  LoRa.setPreambleLength(8);
  LoRa.setGain(6);
}

void receiveMessage(int packetSize)
{
  newMessage = true;
  newPacketSize = packetSize;
}

void onTxDone()
{
  LoRa.receive();
}

void initLoRa()
{
  Serial.println("Initializing LoRa....");

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
  //ctraes128.setKey(key, 16);
  //ctraes128.setIV(key, 16);

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

void checkForMessage(){
  if (newMessage){
    byte data[newPacketSize];
    for (int i = 0; i < newPacketSize; i++){
      data[i] = LoRa.read();
    }

    float rssi = LoRa.packetRssi();
    float snr = LoRa.packetSnr();
    Message *receivedMessage = messageHandler.processNewMessage(data, newPacketSize, rssi, snr);
    if (!receivedMessage->isValid()){
      delete receivedMessage;
      newMessage = false;
      return;
    }
    if (DEBUG)
    {
      Serial.println("Received message:");
      Serial.println("| DESTINATION \t | SENDER \t | MESSAGE ID \t | MAX HOP \t | RSSI \t | SNR \t | MESSAGE \t |");
      Serial.println("##########################################################################################################");
      Serial.println(receivedMessage->toString());
    }

    display.clearDisplay();
    display.setCursor(0, 2);
    display.print("Received:");
    display.setCursor(0, 12);
    display.print(receivedMessage->getMessage());
    display.setCursor(0, 40);
    display.print("RSSI:");
    display.print(rssi);
    display.setCursor(0, 50);
    display.print("SNR:");
    display.print(snr);
    display.display();

    newMessage = false;
    delete receivedMessage;
  }
}

void setup()
{
  Serial.begin(9600);
  Serial.println("Setup LoRa...");
  resetDisplay();
  initializeDisplay();
  initLoRa();
  randomSeed(analogRead(0));
  pinMode(0, INPUT_PULLUP);
}

void loop()
{
  checkForMessage();
  if (!digitalRead(0) && !buttonFlag){
    buttonFlag = true;

    uint32_t byteArraySize;
    byte *bytes = messageHandler.createTextMessage(0xe67e, byteArraySize, "Hello from TTGO LoRa32 v1.0");
    // TODO lookup table for "contacts". Instead of displaying hex addresses in received messages, display names
    //table can contain aes keys also, if we want to encrypt messages uniquely for each contact
    //TODO add message to rebroadcast queue and rebroadcast it X times or until ACK or rebroadcast from another node is received (which comes first)

    LoRa.beginPacket();
    LoRa.write(bytes, byteArraySize);
    LoRa.endPacket(true);
  }
  else if(digitalRead(0) && buttonFlag)
    buttonFlag = false;

  delay(1);
}
