#pragma once
#include <Arduino.h>
#include <SPI.h>
#include <LoRa.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <string.h>


#include "MessageHandler.h"

//TODO move to pins.h
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

#define DEFAULT_CONFIG 1 //TODO move the whole params setting elsewhere