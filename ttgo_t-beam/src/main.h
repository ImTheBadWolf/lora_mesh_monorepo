#pragma once
#include <RadioLib.h>
#include <Crypto.h>
#include <AES.h>
#include <string.h>
#include <CTR.h>

#include "MessageHandler.h"

#define LORA_BAND 868E6

#define MY_ADDRESS 0xE67E
#define DEBUG 1
#define AES_KEY {0x53, 0x69, 0x78, 0x74, 0x65, 0x65, 0x6E, 0x20, 0x62, 0x79, 0x74, 0x65, 0x20, 0x6B, 0x65, 0x79} //"Sixteen byte key"

#define BROADCAST_ADDRESS 0xFFFF
#define HEADER_LENGTH 10
#define TEXTMESSAGE_PREFIX_LENGTH 5
#define SENSORMESSAGE_PREFIX_LENGTH 6