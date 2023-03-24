import secrets  # pylint: disable=no-name-in-module

import socketpool
import wifi
import time
import random
import json

from adafruit_httpserver.mime_type import MIMEType
from adafruit_httpserver.request import HTTPRequest
from adafruit_httpserver.response import HTTPResponse
from adafruit_httpserver.server import HTTPServer
from adafruit_httpserver.server import HTTPMethod

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

sys.path.append("custom_protocol_lib")
import protocol_config
from base_utils import *
from message import Message
from node_process import *
from address_book import AddressBook
import rfm9x_lora

ssid, password = secrets.SSID, secrets.PASSWORD  # pylint: disable=no-member
lastMillis = 0; #TODO just for testing

print("Connecting to", ssid)
wifi.radio.connect(ssid, password)
print("Connected to", ssid)

pool = socketpool.SocketPool(wifi.radio)
server = HTTPServer(pool)

spi_lora = busio.SPI(board.GP10, MOSI=board.GP11, MISO=board.GP12)
CS = digitalio.DigitalInOut(board.GP13)
RESET = digitalio.DigitalInOut(board.GP17)
# 1 => Bw500Cr45Sf128       Short/Fast --X
# 2 => Bw125Cr45Sf128       Short/Slow
# 3 => Bw250Cr47Sf1024      Medium/Fast
# 4 => Bw250Cr46Sf2048      Medium/Slow
# 5 => Bw31_25Cr48Sf512     Long/Fast
# 6 => Bw125Cr48Sf4096      Long/Slow
rfm9x = rfm9x_lora.RFM9x(spi_lora, CS, RESET, 868.0, baudrate=500000)
rfm9x.signal_bandwidth = 500000
rfm9x.coding_rate = 5
rfm9x.spreading_factor = 7
rfm9x.tx_power = 23
rfm9x.preamble_length = 8

def show_info_notification(text):
  print(text)

node_process = NodeProcess(rfm9x, show_info_notification)
address_book = AddressBook("data/contacts.json", "data/sensors.json")
try:
  address_book.add_contact("YOU", f"0x{protocol_config.MY_ADDRESS:04x}")
  address_book.add_contact("ALL", f"0xFFFF") #TODO broadcast functionality not implemented yet
  address_book.add_sensor("YOU", f"0x{protocol_config.MY_ADDRESS:04x}")
  address_book.add_sensor("ALL", f"0xFFFF")
except:
  print("Cant save. Readonly filesystem")

@server.route("/")
def base(request: HTTPRequest):

    with HTTPResponse(request, content_type=MIMEType.TYPE_HTML) as response:
        response.send_file("web/index.html")

@server.route("/sensors")
def sensors_route(request: HTTPRequest):

    with HTTPResponse(request, content_type=MIMEType.TYPE_HTML) as response:
        response.send_file("web/sensors.html")

@server.route("/contacts")
def contacts_route(request: HTTPRequest):

    with HTTPResponse(request, content_type=MIMEType.TYPE_HTML) as response:
        response.send_file("web/contacts.html")

@server.route("/config")
def config_route(request: HTTPRequest):

    with HTTPResponse(request, content_type=MIMEType.TYPE_HTML) as response:
        response.send("Under construction")

#List messages
@server.route("/api/messages")
def api_messages(request: HTTPRequest):
  messages = node_process.get_user_messages()
  parsed_messages = node_process.parse_messages(messages)
  gc.collect()

  data = {
     'messages': parsed_messages
  }
  with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
    response.send(json.dumps(data))

#Create and send new text message
@server.route("/api/send_text_message", method=HTTPMethod.POST)
def api_send_message(request: HTTPRequest):
  try:
    data = json.loads(request.body)
    destination = int(data.get('destination'), 16)
    message = data.get('message')
    message = message[:238] #Limit message length to 238 characters
    max_hop = int(data.get('max_hop'))
    priority = int(data.get('priority'))
    w_ack = data.get('wack')
    node_process.new_text_message(destination, message, w_ack, max_hop, priority)
    gc.collect()
    with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
      response.send("OK")
  except:
    print("Could not parse data")
    with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
      response.send("Could not parse data")

#Resend message
@server.route("/api/resend_message", method=HTTPMethod.POST)
def api_resend_message(request: HTTPRequest):
  try:
    data = json.loads(request.body)
    message_id = int(data.get('message_id'))
    node_process.resend_text_message(message_id)
    gc.collect()
    with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
      response.send("OK")
  except:
    print("Could not parse data")
    with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
      response.send("Could not parse data")

#Create and send new traceroute request
@server.route("/api/traceroute", method=HTTPMethod.POST)
def api_send_traceroute(request: HTTPRequest):
  try:
    data = json.loads(request.body)
    destination = int(data.get('destination'), 16)
    max_hop = int(data.get('max_hop'))
    priority = int(data.get('priority'))
    node_process.new_traceroute_request(destination, max_hop, priority)
    gc.collect()
    with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
      response.send("OK")
  except:
    print("Could not parse data")
    with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
      response.send("Could not parse data")

@server.route("/api/contacts")
def api_contacts(request: HTTPRequest):
  contacts = address_book.get_contacts()

  data = {
     'contacts': contacts
  }
  with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
    response.send(json.dumps(data))

@server.route("/api/contact", method=HTTPMethod.PUT)
def api_add_contact(request: HTTPRequest):
  try:
    data = json.loads(request.body)
    address = data.get('address')
    name = data.get('name')
    address_book.add_contact(name, address)
    with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
      response.send("OK")
  except:
    print("Could not parse data")
    with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
      response.send("Could not parse data")

@server.route("/api/contact", method=HTTPMethod.DELETE)
def api_del_contact(request: HTTPRequest):
  try:
    data = json.loads(request.body)
    address = data.get('address')
    address_book.del_contact(address)
    with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
      response.send("OK")
  except:
    print("Could not parse data")
    with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
      response.send("Could not parse data")

@server.route("/api/sensors")
def api_sensors(request: HTTPRequest):
  sensors = address_book.get_sensors()

  data = {
     'sensors': sensors
  }
  with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
    response.send(json.dumps(data))

@server.route("/api/sensor", method=HTTPMethod.PUT)
def api_add_sensor(request: HTTPRequest):
  try:
    data = json.loads(request.body)
    address = data.get('address')
    name = data.get('name')
    address_book.add_sensor(name, address)
    with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
      response.send("OK")
  except:
    print("Could not parse data")
    with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
      response.send("Could not parse data")

@server.route("/api/sensor", method=HTTPMethod.DELETE)
def api_del_sensor(request: HTTPRequest):
  try:
    data = json.loads(request.body)
    address = data.get('address')
    address_book.del_sensor(address)
    with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
      response.send("OK")
  except:
    print("Could not parse data")
    with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
      response.send("Could not parse data")


print(f"Listening on http://{wifi.radio.ipv4_address}:80")
#server.serve_forever(str(wifi.radio.ipv4_address))

#Start the server.
server.start(str(wifi.radio.ipv4_address))
while True:
  node_process.receive_message() #Adds 100ms delay...
  node_process.tick()

  try:
    """ if lastMillis != 0 and int(time.time() * 1000) - lastMillis > 5000:
      lastMillis = 0
      newState = 'ACK' if random.randint(0,1) == 1 else 'NAK'
      print("Updating message state to: " + newState)
      MOCK_MESSAGE_LIST[-1]['state'] = newState """
    server.poll()
  except OSError as error:
    print(error)
    continue