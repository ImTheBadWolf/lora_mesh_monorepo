// /https://github.com/Xinyuan-LilyGO/LilyGo-LoRa-Series/tree/master/examples/RadioLibExamples/SX1262/SX1262_Receive_Interrupt
#include "main.h"
#include "boards.h"

SX1262 radio = new Module(RADIO_CS_PIN, RADIO_DIO1_PIN, RADIO_RST_PIN, RADIO_BUSY_PIN);
MessageHandler messageHandler = MessageHandler();

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

void memoryAnalyse(){
  Serial.print("\nFree Heap: ");
  Serial.println(ESP.getFreeHeap());
}

void setup()
{
  initBoard();
  delay(1500);
  Serial.print(F("[SX1262] Initializing ... "));

  int state = radio.begin(868.0, 500, 9, 6, RADIOLIB_SX126X_SYNC_WORD_PRIVATE, 10, 16);
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

  Serial.println("[SX1262] Starting to listen ... ");
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
  if (operationDone)
  {
    // disable the interrupt service routine while
    // processing the data
    enableInterrupt = false;
    operationDone = false;

    if(transmitFlag){
      transmitFlag = false;
    }
    else{
      uint32_t packetLength = radio.getPacketLength();
      if (packetLength){
        digitalWrite(BOARD_LED, LED_ON);
        byte data[packetLength];
        int state = radio.readData(data, packetLength);
        if (state == RADIOLIB_ERR_NONE)
        {
          Message* receivedMessage = messageHandler.processNewMessage(data, packetLength, radio.getRSSI(), radio.getSNR());
          if (!receivedMessage->isValid()){
            //delete receivedMessage;
            //return;
          }
          if (DEBUG){
            /* Serial.println("Received message:");
            Serial.println("| DESTINATION \t | SENDER \t | MESSAGE ID \t | MAX HOP \t | RSSI \t | SNR \t | MESSAGE \t |");
            Serial.println("##########################################################################################################");
            Serial.println(receivedMessage->toString()); */
          }
          if (receivedMessage->getSenderAddress() == 0x0004){
            //TODO just for testing
            /* uint32_t byteArraySize;
            byte *bytes = messageHandler.createTextMessage(0x0004, byteArraySize, "Hello from TTGO t-beam");

            transmissionState = radio.startTransmit(bytes, byteArraySize);
            transmitFlag = true; */
          }

          delete receivedMessage;
        }
        digitalWrite(BOARD_LED, LED_OFF);
      }
    }
    if (!transmitFlag){
      radio.startReceive();
    }
    enableInterrupt = true;
  }
}