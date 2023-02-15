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
import sys
import time
import digitalio
import board
import busio
#TODO sort imports, remove unused

sys.path.append("custom_protocol_lib")
import protocol_config
from base_utils import *
from message import Message
import rfm9x_lora

key_set = 0
keypad = adafruit_matrixkeypad.Matrix_Keypad(config.rows, config.cols, config.keys1)
message_to_send = "Hello world from pi pico"

def show_info_notification(text):
  global screen
  screen[2].text = text
  global info_timeout
  info_timeout = round(time.monotonic() * 1000)

def send_message(message):
  msg_object = Message()
  msg_object.new_message(protocol_config.CONTACT, protocol_config.MY_ADDRESS, message, max_hop=13)
  #rfm9x.send(new_message)
  rfm9x.send(msg_object.get_message_bytes())
  show_info_notification("Sent")

def receive_message():
  packet = rfm9x.receive(timeout=0.1)
  if packet is not None:
    message = Message()
    message.construct_message_from_bytes(packet)

    if protocol_config.MONITORING or message.get_destination() == protocol_config.MY_ADDRESS:
      show_info_notification("Received")
      global screen
      screen[6].text = f'Received SNR:{rfm9x.last_snr} RSSI:{rfm9x.last_rssi}'
      screen[7].text = f'From: 0x{message.get_sender():04x}, maxhop: {message.get_max_hop()}'
      screen[8].text = f'{message.get_text_message().decode("utf-8")}'

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
  """ if pressed_key == "alt":
    increment_key_set() """
  if pressed_key == "bsp":
    message_to_send = message_to_send[:-1]
  elif pressed_key == "ent":
    send_message(message_to_send)
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

font_file = "fonts/gomme-20.pcf"
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
        SimpleTextDisplay.YELLOW,
        (176, 196, 245),
        SimpleTextDisplay.WHITE,
        SimpleTextDisplay.WHITE,
        (176, 196, 245),
        SimpleTextDisplay.WHITE,
        SimpleTextDisplay.WHITE,
        SimpleTextDisplay.WHITE,
    ),
)
screen[0].text = "OoogaBooga messenger"
screen[1].text = f'My address: 0x{protocol_config.MY_ADDRESS:04x}'
screen[3].text = f'Message to send(to 0x{protocol_config.CONTACT:04x})'
screen[4].text = message_to_send
screen[6].text = f'Received SNR:{0} RSSI:{0} :'
screen[7].text = ""
screen.show()

#500kBW, 7SF, 4/5CR, 0x34 sync?, 8 preamble length
#TODO load settings from config
rfm9x = rfm9x_lora.RFM9x(spi_lora, CS, RESET, 868.0, baudrate=500000)
rfm9x.signal_bandwidth = 500000
rfm9x.coding_rate = 5
rfm9x.spreading_factor = 7
rfm9x.tx_power = 23
rfm9x.preamble_length = 8
#rfm9x.on_recv = on_recv
#rfm9x.set_mode_rx()
info_timeout = 0

while True:
    keys = keypad.pressed_keys
    #TODO circuit python doesnt support interrupts...
    #https://github.com/adafruit/circuitpython/issues/1380
    r_msg = receive_message()
    if r_msg is not None:
      screen[7].text = r_msg

    if keys:
      handle_key_press(keys[0])
      screen[4].text = message_to_send
      sleep(0.2)

    #Clear notification after 3 seconds
    if info_timeout > 0 and round(time.monotonic() * 1000) - info_timeout > 3000:
      screen[2].text = ""
      info_timeout = 0

    screen.show()
