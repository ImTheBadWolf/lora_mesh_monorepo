// /https://github.com/Xinyuan-LilyGO/LilyGo-LoRa-Series/tree/master/examples/RadioLibExamples/SX1262/SX1262_Receive_Interrupt
#include <RadioLib.h>
#include "boards.h"

SX1262 radio = new Module(RADIO_CS_PIN, RADIO_DIO1_PIN, RADIO_RST_PIN, RADIO_BUSY_PIN);

int transmissionState = RADIOLIB_ERR_NONE;

volatile bool transmitFlag = false;

volatile bool enableInterrupt = true;
volatile bool operationDone = false;

void setFlag(void)
{
  if (!enableInterrupt)
  {
    return;
  }

  // we sent or received  packet, set the flag
  operationDone = true;
}

void setup()
{
  initBoard();
  delay(1500);
  Serial.print(F("[SX1262] Initializing ... "));

  int state = radio.begin(868.0, 500, 7, 5, RADIOLIB_SX126X_SYNC_WORD_PRIVATE, 10, 8);
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

  // set the function that will be called
  // when new packet is received or transmission is finished
  radio.setDio1Action(setFlag);

  // start listening for LoRa packets
  Serial.print(F("[SX1262] Starting to listen ... "));
  state = radio.startReceive();
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
  digitalWrite(BOARD_LED, LED_OFF);
}

void loop()
{
  // check if the flag is set
  if (operationDone)
  {
    // disable the interrupt service routine while
    // processing the data
    enableInterrupt = false;
    operationDone = false;

    if(transmitFlag){
      if (transmissionState == RADIOLIB_ERR_NONE)
        Serial.println(F("transmission finished!"));

      // listen for response
      radio.startReceive();
      transmitFlag = false;
    }else{
      String str;
      int state = radio.readData(str);

      if (state == RADIOLIB_ERR_NONE)
      {
        digitalWrite(BOARD_LED, LED_ON);
        Serial.println(F("[SX1262] Received packet!"));

        Serial.print(F("[SX1262] Data:\t\t"));
        Serial.println(str);

        Serial.print(F("[SX1262] RSSI:\t\t"));
        Serial.print(radio.getRSSI());
        Serial.println(F(" dBm"));

        Serial.print(F("[SX1262] SNR:\t\t"));
        Serial.print(radio.getSNR());
        Serial.println(F(" dB"));

        delay(1000);
        Serial.print(F("[SX1262] Sending another packet ... "));
        transmissionState = radio.startTransmit(str + "R");
        transmitFlag = true;
        digitalWrite(BOARD_LED, LED_OFF);
      }
    }
    enableInterrupt = true;
  }
}