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
from node_process import *
import rfm9x_lora

key_set = 0
keypad = adafruit_matrixkeypad.Matrix_Keypad(config.rows, config.cols, config.keys1)
TMP_CONTACT = 0x0005
received_counter = 0
sent_counter = 0

config = protocol_config.ProtocolConfig('data/settings.json')
initialised = config.is_initialised()

if not initialised:
  print("My address not set. Please edit data/settings.json and set MY_ADDRESS")
  sys.exit()

message_to_send = f'Hello world from 0x{config.MY_ADDRESS:04X}'

def show_info_notification(text):
  global screen
  screen[2].text = text
  global info_timeout
  info_timeout = round(time.monotonic() * 1000)

def handle_key_press(pressed_key):
  global message_to_send
  if pressed_key == "alt":
    node_process.new_sensor_message(TMP_CONTACT, f"Sensor value: {random.randint(0, 100)}")
    global sent_counter
    sent_counter += 1
    screen[0].text = f"received:{received_counter} sent:{sent_counter}"
  elif pressed_key == "z":
    node_process.new_traceroute_request(TMP_CONTACT)
  elif pressed_key == "bsp":
    message_to_send = message_to_send[:-1]
  elif pressed_key == "ent":
    node_process.new_text_message(TMP_CONTACT, message_to_send, w_ack = True)
    global sent_counter
    sent_counter += 1
    screen[0].text = f"received:{received_counter} sent:{sent_counter}"
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
screen[0].text = "Messenger 3000"
screen[1].text = f'My address: 0x{config.MY_ADDRESS:04X}'
screen[3].text = f'Message to send(to 0x{TMP_CONTACT:04X})'
screen[4].text = message_to_send
screen[6].text = f'Received SNR:{0} RSSI:{0} :'
screen[7].text = ""
screen.show()

#TODO load settings from config
rfm9x = rfm9x_lora.RFM9x(spi_lora, CS, RESET, 868.0, baudrate=500000)
rfm9x.signal_bandwidth = 500000
rfm9x.coding_rate = 5
rfm9x.spreading_factor = 7
rfm9x.tx_power = 23
rfm9x.preamble_length = 8
info_timeout = 0

node_process = NodeProcess(rfm9x, show_info_notification, config)
counter = 0
while True:
    start_time = round(time.monotonic() * 1000)
    keys = keypad.pressed_keys
    node_process.tick()
    r_msg = node_process.get_latest_message()

    if r_msg is not None:
      (msg_instance, snr, rssi) = r_msg
      received_counter += 1
      screen[0].text = f"received:{received_counter} sent:{sent_counter}"
      screen[6].text = f'Received SNR:{snr} RSSI:{rssi}'

      if msg_instance.get_message_type() == MessageType.SENSOR_DATA:
        screen[7].text = f'From: 0x{msg_instance.get_sender():04x}, ttl: {msg_instance.get_ttl()}'
        screen[8].text = f'{msg_instance.get_sensor_data().decode("utf-8")}'
        screen[9].text = f'This was sensor message'
      elif msg_instance.get_message_type() == MessageType.TRACEROUTE_REQUEST:
        screen[7].text = f'From: 0x{msg_instance.get_sender():04x}, maxhop: {msg_instance.get_maxHop()}'
        screen[8].text = "Traceroute request received"
        screen[9].text = f'Initial maxhop:{msg_instance.get_initialMaxHop()}'
      elif msg_instance.get_message_type() == MessageType.TRACEROUTE:
        screen[7].text = f'From: 0x{msg_instance.get_sender():04x}, maxhop: {msg_instance.get_maxHop()}'
        screen[8].text = f'{msg_instance.get_text_message().decode("utf-8")}'
        screen[9].text = f'Traceroute'
      else:
        screen[7].text = f'From: 0x{msg_instance.get_sender():04x}, maxhop: {msg_instance.get_maxHop()}'
        screen[8].text = f'{msg_instance.get_text_message().decode("utf-8")}'
        screen[9].text = f'Initial maxhop:{msg_instance.get_initialMaxHop()}'
      screen[10].text = f'Msg ID:{msg_instance.get_message_id()}'

    if keys:
      handle_key_press(keys[0])
      screen[4].text = message_to_send

    #Clear notification after 3 seconds
    if info_timeout > 0 and round(time.monotonic() * 1000) - info_timeout > 3000:
      screen[2].text = ""
      info_timeout = 0

    end_time = round(time.monotonic() * 1000)
    """ print(f'Loop time: {end_time - start_time}')
    counter += 1
    if counter > 25:
      exit() """
    #Loop time ~30ms, ~80ms when receiving a message while using rfm9x.receive() with timeout 0.025
    #screen.show()
