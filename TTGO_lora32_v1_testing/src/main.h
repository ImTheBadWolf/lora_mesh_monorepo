#pragma once
#include <Arduino.h>
#include <SPI.h>
#include <LoRa.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Crypto.h>
#include <AES.h>
#include <string.h>
#include <CTR.h>

#include "LoraHandler.h"

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

#define MY_ADDRESS 0xA02C

#define BROADCAST_ADDRESS 0xFFFF
#define HEADER_LENGTH 10
#define TEXTMESSAGE_PREFIX_LENGTH 5
#define SENSORMESSAGE_PREFIX_LENGTH 6