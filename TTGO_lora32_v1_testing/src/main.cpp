#include <Arduino.h>
// LoRa include
#include <SPI.h>
#include <LoRa.h>
// display include
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Crypto.h>
#include <AES.h>
#include <string.h>
#include <CTR.h>

// Define OLED PIN
#define OLED_SDA 4
#define OLED_SCL 15
#define OLED_RST 16
// LoRa pins
#define LORA_MISO 19
#define LORA_CS 18
#define LORA_MOSI 27
#define LORA_SCK 5
#define LORA_RST 14
#define LORA_IRQ 26

#define LORA_BAND 868E6

int counter = 0;
bool buttonFlag = false;
Adafruit_SSD1306 display(128, 64, &Wire, OLED_RST);
CTR<AES128> ctraes128;
byte key[16] = {0x53, 0x69, 0x78, 0x74, 0x65, 0x65, 0x6E, 0x20, 0x62, 0x79, 0x74, 0x65, 0x20, 0x6B, 0x65, 0x79}; //"Sixteen byte key"

void resetDisplay()
{
  digitalWrite(OLED_RST, LOW);
  delay(25);
  digitalWrite(OLED_RST, HIGH);
}
void initializeDisplay()
{
  Serial.println("Initializing display...");

  Wire.begin(OLED_SDA, OLED_SCL);
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3c))
  {
    Serial.println("Failed to initialize the display");
    for (;;)
      ;
  }
  Serial.println("Display initialized");
  display.clearDisplay();

  display.setTextColor(WHITE);
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.println("Welcome to LORA");

  display.setTextSize(1);
  display.println("Lora thingy");
  display.display();
}
void initLoRa()
{
  Serial.println("Initializing LoRa....");
  SPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_CS);
  LoRa.setPins(LORA_CS, LORA_RST, LORA_IRQ);
  // Start LoRa using the frequency
  int result = LoRa.begin(LORA_BAND);

  if (result != 1)
  {
    display.setCursor(0, 10);
    display.println("Failed to start LoRa network!");
    for (;;)
      ;
  }

  LoRa.setSignalBandwidth(500E3);
  LoRa.setSpreadingFactor(7);
  LoRa.setCodingRate4(5);
  LoRa.setSyncWord(0x12);
  LoRa.setPreambleLength(8);
  LoRa.setGain(6);

  Serial.println("LoRa initialized");
  display.display();
  delay(500);
  display.setCursor(0, 15);
  display.println("LoRa network OK!");
  display.display();
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
  LoRa.endPacket();
}

void sendMessage(String message){
  byte messageByteArr[message.length()+1];
  message.getBytes(messageByteArr, message.length()+1);

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
      3
    };
  byte input[message.length()+7];
  byte output[message.length()+7];

  for(int i=0; i<message.length(); i++){
    input[i] = messageByteArr[i];
  }
  for (int i = message.length(); i < message.length()+7; i++)
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
  LoRa.endPacket();
}

void setup()
{
  Serial.begin(9600);
  Serial.println("Setup LoRa...");
  resetDisplay();
  initializeDisplay();
  initLoRa();
  ctraes128.setKey(key, 16);
  ctraes128.setIV(key, 16);
  pinMode(0, INPUT_PULLUP);
}

void loop()
{
  if (!digitalRead(0) && !buttonFlag){
    buttonFlag = true;
    sendMessage("OogaBooga");
  }
  else if(digitalRead(0) && buttonFlag)
    buttonFlag = false;

  int packetSize = LoRa.parsePacket();
  if (packetSize)
  {
    Serial.print("Received packet: ");
    String msg = "";
    int data[packetSize];

    int rssi = LoRa.packetRssi();
    int i = 0;
    while (LoRa.available())
    {
      int c = LoRa.read();
      Serial.print(c,HEX);
      Serial.print(" ");
      data[i] = c;
      i++;
      //msg += (char)c;
    }
    Serial.println();
    if (data[16] == 33 || data[3] != 0x22)
    { // Symbol "!" for delivery confirmation
      return;
    }

    byte strippedData[packetSize-16];
    byte output[packetSize - 16];
    for(int i=0;i<packetSize-16; i++){
      strippedData[i] = data[16+i];
    }
    ctraes128.setKey(key, 16);
    ctraes128.setIV(key, 16);
    ctraes128.decrypt(output, strippedData, packetSize-16);
    Serial.print("\nDecrypted: ");
    for (int i = 0; i < packetSize - 16; i++)
    {
      if (output[i] != 0x7C)
        msg += (char)output[i];
      Serial.print(output[i], HEX);
      Serial.print(" ");
    }
    Serial.println();
    Serial.println(msg);

    // key : 53 69 78 74 65 65 6E 20 62 79 74 65 20 6B 65 79
    // IV: 53 69 78 74 65 65 6E 20 62 79 74 65 20 6B 65 79
    //Mode ctr, aes128, first 16 bytes are addressing

    display.clearDisplay();
    display.setCursor(0, 2);
    display.print("Received:");
    display.setCursor(0, 12);
    display.print(msg);
    display.setCursor(0, 40);
    display.print("RSSI:");
    display.print(rssi);

    display.display();
    delay(700);
    sendConfirmation(data[8], data[9], data[10], data[11]);
    delay(200);
    if (msg == "Ping")
    {
      sendMessage("Pong");
    }
  }
  delay(1);
}
