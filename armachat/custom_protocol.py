import os
from adafruit_bitmap_font import bitmap_font
from time import sleep
import microcontroller
from adafruit_simple_text_display import SimpleTextDisplay
from adafruit_display_text import label
from config import config
import adafruit_matrixkeypad
import displayio
from digitalio import DigitalInOut
import pwmio
from adafruit_display_text import label
from adafruit_st7789 import ST7789
from digitalio import DigitalInOut, Pull
import board
import busio
import terminalio
import ulora
import analogio
from binascii import hexlify
import digitalio
import gc
import aesio
import random

key_set = 0
message_to_send = ""
received_msg = "TODO"
keypad = adafruit_matrixkeypad.Matrix_Keypad(config.rows, config.cols, config.keys1)

HEADER_LENGTH = 12
TEXTMESSAGE_PREFIX_LENGTH = 5
MY_ADDRESS = 0xA62C
AES_KEY = "SuperTajne heslo"#TODOconfig.password

def calculate_checksum(header):
  #Calculates CRC-16/CCITT-FALSE checksum of first 8 bytes of data
  crc = 0xFFFF
  polynomial = 0x1021
  for byte in header[0:8]:
    crc ^= byte << 8
    for bit in range(0, 8):
      if crc & 0x8000:
        crc = (crc << 1) ^ polynomial
      else:
        crc <<= 1
  return crc & 0xFFFF

def create_header(destinationAddress, senderAddress,  messageType=0, priority=0):
  header = bytearray(HEADER_LENGTH)

  destination = destinationAddress.to_bytes(2, 'big')
  header[0] = destination[0] #TODO check if endianess is correct
  header[1] = destination[1]

  sender = senderAddress.to_bytes(2, 'big')
  header[2] = sender[0]
  header[3] = sender[1]

  header[4] = random.randint(0, 255)
  header[5] = random.randint(0, 255)
  header[6] = random.randint(0, 255)
  header[7] = random.randint(0, 255)

  checksum = calculate_checksum(header)
  checksum = checksum.to_bytes(2, 'big')
  header[8] = checksum[0]
  header[9] = checksum[1]

  header[10] = messageType
  header[11] = priority

  return header

def create_text_message(destinationAddress, message, receiveAck=False, maxHop=5, priority=0):
  header = create_header(destinationAddress, MY_ADDRESS, 1 if receiveAck else 0, priority)
  message_prefix = bytearray(TEXTMESSAGE_PREFIX_LENGTH)# TODO only for text messages !

  #TODO for compatibility adding 4 bytes of random data, this will be removed later

  message_prefix[0] = 1#random.randint(0, 255)
  message_prefix[1] = 2#random.randint(0, 255)
  message_prefix[2] = 3#random.randint(0, 255)
  message_prefix[3] = 4#random.randint(0, 255)

  message_prefix[4] = maxHop

  #encrypt message with aes and combine with header and return
  encrypted_message = bytearray(len(message))
  cipher = aesio.AES(AES_KEY, aesio.MODE_CTR, AES_KEY)
  cipher.encrypt_into(bytes(message, "utf-8"), encrypted_message)

  return list(header) + list(message_prefix) + list(encrypted_message)

def send_message():
  new_message = create_text_message(0xE67E, "Hello from armachat")
  rfm9x.send(new_message)

  global message_to_send
  message_to_send = "Sent"

def receive_message():
  out = None
  packet = rfm9x.receive(timeout=0.1)
  if packet is not None:

    message_prefix_length = TEXTMESSAGE_PREFIX_LENGTH #TODO this length depends on message type (data[10])
    encrypted_message = bytes(packet[HEADER_LENGTH + message_prefix_length:])
    # Decrypt
    cipher = aesio.AES(AES_KEY, aesio.MODE_CTR, AES_KEY)
    outp = bytearray(len(encrypted_message))
    cipher.encrypt_into(encrypted_message, outp)
    try:
      out = str(outp, "utf-8")
    except UnicodeError:
      print("error")

  return out

def get_char_set_label():
  if(key_set == 0):
    return "abc"
  elif(key_set == 1):
    return "123"
  elif(key_set == 2):
    return "ABC"

def increment_key_set():
  global key_set
  key_set += 1
  if key_set == 3:
    key_set = 0
  global keypad
  if(key_set == 0):
    keypad = adafruit_matrixkeypad.Matrix_Keypad(config.rows, config.cols, config.keys1)
  elif(key_set == 1):
    keypad = adafruit_matrixkeypad.Matrix_Keypad(config.rows, config.cols, config.keys2)
  elif(key_set == 2):
    keypad = adafruit_matrixkeypad.Matrix_Keypad(config.rows, config.cols, config.keys3)

def handle_key_press(pressed_key):
  global message_to_send
  if pressed_key == "alt":
    increment_key_set()
  elif pressed_key == "bsp":
    message_to_send = message_to_send[:-1]
  elif pressed_key == "ent":
    send_message()
  else:
    message_to_send += pressed_key

displayio.release_displays()

tft_cs = board.GP21
tft_dc = board.GP16
spi_mosi = board.GP19
spi_clk = board.GP18
spi = busio.SPI(spi_clk, spi_mosi)
spi_lora = busio.SPI(board.GP10, MOSI=board.GP11, MISO=board.GP12)
backlight = board.GP20
CS = digitalio.DigitalInOut(board.GP13)
RESET = digitalio.DigitalInOut(board.GP17)

font_file = "fonts/neep-24.pcf"
font = bitmap_font.load_font(font_file)

display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs)
display = ST7789(display_bus, rotation=270, width=320, height=240, backlight_pin=backlight)
splash = displayio.Group()
display.show(splash)


screen = SimpleTextDisplay(
    display=display,
    font=font,
    title_scale=1,
    text_scale=1,
    colors=(
        SimpleTextDisplay.BLUE,
        SimpleTextDisplay.GREEN,
        SimpleTextDisplay.WHITE,
        SimpleTextDisplay.WHITE,
    ),
)
screen[0].text = "OoogaBooga messenger"
screen[1].text = "Character set: " + get_char_set_label() + " (ALT)"
screen[2].text = "Message:"
screen[3].text = message_to_send
screen[7].text = "Receved:"
screen[8].text = received_msg
screen.show()

#500kBW, 7SF, 4/5CR, 0x34 sync?, 8 preamble length
#TODO load settings from config
#TODO find out how to make event listener for received lora packets. When new packed is received, interupt is fired and new message is processed
#TODO use newer version of u-lora https://github.com/martynwheeler/u-lora
#lora.on_recv
rfm9x = ulora.LoRa(spi_lora, CS, freq=868.0, modem_config=(0x92, 0x74, 0x04), tx_power=config.power)

while True:

    r_msg = receive_message()
    keys = keypad.pressed_keys
    if keys:
      handle_key_press(keys[0])

    if r_msg:
      screen[8].text = r_msg

    screen[1].text = "Character set: " + get_char_set_label() + " (ALT)"
    screen[3].text = message_to_send
    screen.show()
    sleep(0.2)
