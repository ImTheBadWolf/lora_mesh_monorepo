#include "main.h"

#ifdef __cplusplus
extern "C" {
#endif
uint8_t temprature_sens_read();
#ifdef __cplusplus
}
#endif
uint8_t temprature_sens_read();


Adafruit_SSD1306 display(128, 64, &Wire, OLED_RST);
MessageHandler messageHandler = MessageHandler();
Array<QueueItem *, 500> messageQueue;
Array<uint8_t, 500> itemsToRemove;
int32_t lastMillis = INT32_MIN;
bool buttonFlag = true;
bool txDoneFlag = true;

union twoByte2
{
  uint16_t value;
  unsigned char Bytes[2];
} twoByteVal2;

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
  display.display();
}

void setSettings()
{
  LoRa.setSignalBandwidth(LORA_BW * 1000);
  LoRa.setSpreadingFactor(LORA_SF);
  LoRa.setCodingRate4(LORA_CR);

  // Default, do not change
  LoRa.setSyncWord(0x12);
  LoRa.setPreambleLength(8);
  LoRa.setGain(6);
}

void onTxDone() {
  txDoneFlag = true;
}

void onReceive(int packetSize) {
  //Dont really need this, but it will be used to delay sending if the channel is busy
  if (packetSize == 0)
    return;

  String incoming = "";
  while (LoRa.available()) {                                // can't use readString() in callback, so
    incoming += (char)LoRa.read(); // add bytes one by one
  }
}

void initLoRa() {
  Serial.println("Initializing LoRa....");

  SPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_CS);
  LoRa.setPins(LORA_CS, LORA_RST, LORA_IRQ);

  int result = LoRa.begin(868E6);
  if (result != 1)
  {
    display.setCursor(0, 10);
    display.println("Failed to start LoRa network!");
    for (;;)
      ;
  }

  setSettings();

  Serial.println("LoRa initialized");
  display.display();
  delay(500);
  display.setCursor(0, 0);
  display.println("My Address: " + String(MY_ADDRESS, HEX));
  display.display();
  delay(500);
  LoRa.onReceive(onReceive);
  LoRa.onTxDone(onTxDone);
  LoRa.receive();
}

void createSensorMessage()
{
  int hallValue = hallRead();
  // For each contact in CONTACTS[] create sensor message
  for (int i = 0; i < sizeof(CONTACTS) / sizeof(uint16_t); i++)
  {
    uint32_t byteArraySize;
    String message = "Hall effect sensor value: " + String(hallValue) + "\nFree heap: " + String(ESP.getFreeHeap()) + "B\nUptime: " + String(millis() / 1000/ 60) + " Minutes";

    byte *bytes = messageHandler.createSensorMessage(CONTACTS[i], byteArraySize, message);
    messageQueue.push_back(new QueueItem(0, RESEND_COUNT, bytes, byteArraySize));
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
  delay(1000);
}

void loop()
{
  // Call createSensorMessage() if button is pressed
  if (!digitalRead(0) && !buttonFlag){
    buttonFlag = true;
    createSensorMessage();
  }
  else if(digitalRead(0) && buttonFlag)
    buttonFlag = false;

  // Call createSensorMessage() if SEND_INTERVAL has passed
  if (millis() - lastMillis > SEND_INTERVAL * 1000){
    lastMillis = millis();
    createSensorMessage();
  }

  for (int i = 0; i < messageQueue.size(); i++){
    QueueItem *item = messageQueue[i];
    if (txDoneFlag && millis() > item->getTimeout()) {
      if (item->getResendCounter() > 0) {
        item->decrementResendCounter();
        item->setTimeout(millis() + RESEND_TIMEOUT * 1000);
        byte *byteArr = item->getPayloadBytes();
        u_int8_t size = item->getPayloadBytesSize();

        LoRa.beginPacket();
        LoRa.write(byteArr, size);
        LoRa.endPacket(true);
        txDoneFlag = false;
        delay(150);
        LoRa.receive();
      }
      else{
        // Counter is 0, remove from queue
        itemsToRemove.push_back(i);
      }
    }
  }
  // Remove items from queue
  // While loop in itemsToRemove is necessary because removing items from queue changes the size of the queue
  while (itemsToRemove.size() > 0){
    // Find the highest index to remove first
    uint8_t highestIndex = 0;
    for (int i = 0; i < itemsToRemove.size(); i++){
      if (itemsToRemove[i] > itemsToRemove[highestIndex])
        highestIndex = i;
    }
    QueueItem *item = messageQueue[itemsToRemove[highestIndex]];
    byte *byteArr = item->getPayloadBytes();
    messageQueue.remove(itemsToRemove[highestIndex]);
    delete byteArr;
    delete item;
    itemsToRemove.remove(highestIndex);
  }
  itemsToRemove.clear();
}