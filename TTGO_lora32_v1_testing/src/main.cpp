#include "main.h"

bool buttonFlag = false;

Adafruit_SSD1306 display(128, 64, &Wire, OLED_RST);


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

void setup()
{
  Serial.begin(9600);
  Serial.println("Setup LoRa...");
  resetDisplay();
  initializeDisplay();
  initLoRa(display);
  pinMode(0, INPUT_PULLUP);
}

void loop()
{
  checkForMessage();
  if (!digitalRead(0) && !buttonFlag){
    buttonFlag = true;
    sendMessage("OogaBooga");
  }
  else if(digitalRead(0) && buttonFlag)
    buttonFlag = false;

  delay(1);
}
