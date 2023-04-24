// TTGO T-beam T22_V1.1
#include <SparkFun_Ublox_Arduino_Library.h>
#include <MicroNMEA.h>
#include "main.h"
#include "boards.h"
#include <axp20x.h>

char nmeaBuffer[100];
MicroNMEA nmea(nmeaBuffer, sizeof(nmeaBuffer));
SFE_UBLOX_GPS myGPS;
SX1262 radio = new Module(RADIO_CS_PIN, RADIO_DIO1_PIN, RADIO_RST_PIN, RADIO_BUSY_PIN);
AXP20X_Class axp;

MessageHandler messageHandler = MessageHandler();
Array<QueueItem *, 500> messageQueue;
Array<uint8_t, 500> itemsToRemove;

int transmissionState = RADIOLIB_ERR_NONE;
volatile bool transmittedFlag = false;
volatile bool enableInterrupt = true;
int32_t lastMillis = INT32_MIN;

void setFlag(void){
  if (!enableInterrupt)
    return;
  // we sent  packet, set the flag
  transmittedFlag = true;
}

void createSensorMessage() {
  float lat, lon;
  myGPS.checkUblox(); // See if new data is available. Process bytes as they come in.

  if (nmea.isValid() == true){
    lat = nmea.getLatitude() / 1000000.;
    lon = nmea.getLongitude() / 1000000.;
  }
  else {
    // No fix
    // Get random latitude and longitude in Slovakia if RANDOM_GPS is defined
    #ifndef RANDOM_GPS
      return;
    #endif

    // Serial.print("Nofix");
    // Serial.println(nmea.getNumSatellites());
    lat = random(48000000, 49000000) / 1000000.0;
    lon = random(17000000, 18000000) / 1000000.0;
  }
  // Serial.println("Lat: " + String(lat) + ", Lon: " + String(lon));
  // For each contact in CONTACTS[] create sensor message
  for (int i = 0; i < sizeof(CONTACTS) / sizeof(uint16_t); i++)
  {
    uint32_t byteArraySize;
    String message = "GPS: " + String(lat) + ", " + String(lon);
    byte *bytes = messageHandler.createSensorMessage(CONTACTS[i], byteArraySize, message);
    messageQueue.push_back(new QueueItem(0, RESEND_COUNT, bytes, byteArraySize));
  }
}

void setup()
{
  Wire.begin(21, 22);
  if (!axp.begin(Wire, AXP192_SLAVE_ADDRESS))
  {
    Serial.println("AXP192 Begin PASS");
  }
  else
  {
    Serial.println("AXP192 Begin FAIL");
  }
  axp.setPowerOutPut(AXP192_LDO3, AXP202_ON); //Power ON GPS

  initBoard();
  delay(1500);
  Serial.print(F("[SX1262] Initializing ... "));

  int state = radio.begin(868.0, LORA_BW, LORA_SF, LORA_CR, RADIOLIB_SX126X_SYNC_WORD_PRIVATE, 22, 8);
  if (state == RADIOLIB_ERR_NONE)
  {
    Serial.println(F("success!"));
  }
  else
  {
    Serial.print(F("failed, code "));
    Serial.println(state);
    while (true)
      ;
  }

  radio.setDio1Action(setFlag);

  do
  {
    if (myGPS.begin(Serial1))
    {
      Serial.println("Connected to GPS");
      myGPS.setUART1Output(COM_TYPE_NMEA); // Set the UART port to output NMEA only
      myGPS.saveConfiguration();           // Save the current settings to flash and BBR
      Serial.println("GPS serial connected, output set to NMEA");
      break;
    }
    delay(1000);
  } while (1);

  digitalWrite(BOARD_LED, LED_OFF);
}

void loop()
{
  // Call createSensorMessage() if SEND_INTERVAL has passed
  if (millis() - lastMillis > SEND_INTERVAL*1000) {
    lastMillis = millis();
    createSensorMessage();
  }

  for (int i = 0; i < messageQueue.size(); i++){
    QueueItem *item = messageQueue[i];
    if (transmittedFlag && millis() > item->getTimeout()){
      if (item->getResendCounter() > 0){
        digitalWrite(BOARD_LED, LED_ON);
        item->decrementResendCounter();
        item->setTimeout(millis() + RESEND_TIMEOUT * 1000);

        enableInterrupt = false;
        transmittedFlag = false;
        byte *byteArr = item->getPayloadBytes();
        u_int8_t size = item->getPayloadBytesSize();
        int state = radio.startTransmit(byteArr, size);
        enableInterrupt = true;
        digitalWrite(BOARD_LED, LED_OFF);
      }
      else {
        //Counter is 0, remove from queue
        itemsToRemove.push_back(i);
      }
    }
  }
  // Remove items from queue
  // While loop in itemsToRemove is necessary because removing items from queue changes the size of the queue
  while (itemsToRemove.size() > 0) {
    //Find the highest index to remove first
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
void SFE_UBLOX_GPS::processNMEA(char incoming)
{
  nmea.process(incoming);
}