from adafruit_httpserver.mime_type import MIMEType
from adafruit_httpserver.request import HTTPRequest
from adafruit_httpserver.response import HTTPResponse
from adafruit_httpserver.server import HTTPMethod
from adafruit_httpserver.server import HTTPServer
from binascii import hexlify
from time import sleep
import board
import board
import busio
import busio
import digitalio
import digitalio
import gc
import json
import microcontroller
import microcontroller
import socketpool
import sys
import wifi

sys.path.append("custom_protocol_lib")
import protocol_config
from base_utils import *
from node_process import NodeProcess
from address_book import AddressBook
import rfm9x_lora

lastMillis = 0; #TODO just for testing
ssid = None
wifi_connected = False
my_ip = None

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

config = protocol_config.ProtocolConfig('data/settings.json')
initialised = config.is_initialised()

networks = config.get_networks()
for network in networks:
  if network['AP'] != True:
    try:
      ssid = network['SSID']
      wifi.radio.connect(ssid, network['PASSWORD'])
      print("Connected to:", ssid)
      my_ip = wifi.radio.ipv4_address
      wifi_connected = True
      break
    except:
      print("Failed to connect to:", ssid)

if not wifi_connected:
  print("No networks found, starting AP mode")
  #find network which hash ["AP"] = true in networks
  for network in networks:
    if network['AP'] == True:
      try:
        ssid = network['SSID']
        wifi.radio.start_ap(ssid, network['PASSWORD'])
        print(f"Started AP: {ssid} password: {network['PASSWORD']}")
        my_ip = wifi.radio.ipv4_address_ap
        wifi_connected = True
        break
      except Exception as e:
        print("Failed to start AP:", ssid)
        print(e)

pool = socketpool.SocketPool(wifi.radio)
server = HTTPServer(pool)

if initialised:
  node_process = NodeProcess(rfm9x, show_info_notification, config)
  address_book = AddressBook("data/contacts.json", "data/sensors.json")
  try:
    address_book.add_contact("YOU", f"0x{config.MY_ADDRESS:04x}")
    address_book.add_contact("ALL", f"0x{config.BROADCAST_ADDRESS:04x}")
    address_book.add_sensor("YOU", f"0x{config.MY_ADDRESS:04x}")
    address_book.add_sensor("ALL", f"0x{config.BROADCAST_ADDRESS:04x}")
  except:
    print("Cant save. Readonly filesystem")

else:
  print("Not initialised, set your address first. Then restart the device.")

@server.route("/")
def base(request: HTTPRequest):
  if not initialised:
    with HTTPResponse(request, content_type=MIMEType.TYPE_HTML) as response:
      response.send_file("web/config.html")
  else:
    with HTTPResponse(request, content_type=MIMEType.TYPE_HTML) as response:
      response.send_file("web/index.html")

@server.route("/sensors")
def sensors_route(request: HTTPRequest):
  if not initialised:
    with HTTPResponse(request, content_type=MIMEType.TYPE_HTML) as response:
      response.send_file("web/config.html")
  else:
    with HTTPResponse(request, content_type=MIMEType.TYPE_HTML) as response:
      response.send_file("web/sensors.html")

@server.route("/contacts")
def contacts_route(request: HTTPRequest):
  if not initialised:
    with HTTPResponse(request, content_type=MIMEType.TYPE_HTML) as response:
      response.send_file("web/config.html")
  else:
    with HTTPResponse(request, content_type=MIMEType.TYPE_HTML) as response:
      response.send_file("web/contacts.html")

@server.route("/config")
def config_route(request: HTTPRequest):
  with HTTPResponse(request, content_type=MIMEType.TYPE_HTML) as response:
    response.send_file("web/config.html")

#List messages
@server.route("/api/messages")
def api_messages(request: HTTPRequest):
  if initialised:
    messages = node_process.get_user_messages()
    parsed_messages = parse_messages(messages, config)
    gc.collect()

    try:
      page = request.query_params.get("page")
    except:
      page = None
    if page is None:
      page = 0
    else:
      page = int(page)

    page_size = 5
    num_pages = (len(parsed_messages)-1) // page_size + 1

    data = {
      'messages': parsed_messages[page*page_size:(page+1)*page_size],
      'pages': num_pages,
      'total': len(parsed_messages),
    }
    with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
      try:
        response.send(json.dumps(data))
      except MemoryError as e:
        print(e)
        print(f"Free memory: {gc.mem_free()} page: {page} len: {len(data['messages'])}")
        print(f"Allocated memory: {gc.mem_alloc()}")

#Create and send new text message
@server.route("/api/send_text_message", method=HTTPMethod.POST)
def api_send_message(request: HTTPRequest):
  if initialised:
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
  if initialised:
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
  if initialised:
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
  if initialised:
    contacts = address_book.get_contacts()

    data = {
      'contacts': contacts
    }
    with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
      response.send(json.dumps(data))

@server.route("/api/contact", method=HTTPMethod.PUT)
def api_add_contact(request: HTTPRequest):
  if initialised:
    try:
      data = json.loads(request.body)
      address = data.get('address')
      name = data.get('name')
      address_book.add_contact(name, address)
      with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
        response.send("OK")
    except:
      print("Could not parse data, or save file")
      with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
        response.send("Could not parse data, or save file")

@server.route("/api/contact", method=HTTPMethod.DELETE)
def api_del_contact(request: HTTPRequest):
  if initialised:
    try:
      data = json.loads(request.body)
      address = data.get('address')
      address_book.del_contact(address)
      with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
        response.send("OK")
    except:
      print("Could not parse data, or save file")
      with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
        response.send("Could not parse data, or save file")

@server.route("/api/sensors")
def api_sensors(request: HTTPRequest):
  if initialised:
    sensors = address_book.get_sensors()

    data = {
      'sensors': sensors
    }
    with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
      response.send(json.dumps(data))

@server.route("/api/sensor", method=HTTPMethod.PUT)
def api_add_sensor(request: HTTPRequest):
  if initialised:
    try:
      data = json.loads(request.body)
      address = data.get('address')
      name = data.get('name')
      address_book.add_sensor(name, address)
      with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
        response.send("OK")
    except:
      print("Could not parse data, or save file")
      with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
        response.send("Could not parse data, or save file")

@server.route("/api/sensor", method=HTTPMethod.DELETE)
def api_del_sensor(request: HTTPRequest):
  if initialised:
    try:
      data = json.loads(request.body)
      address = data.get('address')
      address_book.del_sensor(address)
      with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
        response.send("OK")
    except:
      print("Could not parse data, or save file")
      with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
        response.send("Could not parse data, or save file")

#Dump message queue
@server.route("/api/dump")
def api_dump(request: HTTPRequest):
  if initialised:
    message_queue = node_process.get_message_queue()
    parsed_message_queue = parse_message_queue(message_queue)
    gc.collect()

    try:
      page = request.query_params.get("page")
    except:
      page = None
    if page is None:
      page = 0
    else:
      page = int(page)

    page_size = 1
    num_pages = (len(parsed_message_queue)-1) // page_size + 1

    data = {
      'messages': parsed_message_queue[page*page_size:(page+1)*page_size],
      'pages': num_pages,
      'total': len(parsed_message_queue),
    }
    with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
      try:
        response.send(json.dumps(data))
      except MemoryError as e:
        print(e)
        print(f"Free memory: {gc.mem_free()} page: {page} len: {len(data['messages'])}")
        print(f"Allocated memory: {gc.mem_alloc()}")

@server.route("/api/config")
def api_config(request: HTTPRequest):
  data = {
    'config': config.get_config(),
  }
  with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
    response.send(json.dumps(data))

@server.route("/api/config", method=HTTPMethod.PUT)
def api_update_config(request: HTTPRequest):
  data = json.loads(request.body)
  try:
    new_config = data.get('config')
    config.update_config(new_config)
    with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
      response.send("OK")
    if config.is_reboot_required():
      print("Rebooting")
      sleep(1)
      microcontroller.reset()
  except Exception as e:
    print("Could not parse data, or save file ")
    print(e)
    with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
      response.send(f"Could not parse data, or save file\n{str(e)}")

@server.route("/api/networks")
def api_networks(request: HTTPRequest):
  data = {
    'networks': config.get_networks(),
    'current': {
      'ssid': ssid,
      'ipv4': str(wifi.radio.ipv4_address)
    }
  }
  with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
    response.send(json.dumps(data))

@server.route("/api/network", method=HTTPMethod.PUT)
def api_add_network(request: HTTPRequest):
  data = json.loads(request.body)
  try:
    network = data.get('network')
    config.add_network(network)
    with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
      response.send("OK")
  except Exception as e:
    print("Could not parse data, or save file ")
    print(e)
    with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
      response.send(f"Could not parse data, or save file\n{str(e)}")

@server.route("/api/network", method=HTTPMethod.DELETE)
def api_remove_network(request: HTTPRequest):
  data = json.loads(request.body)
  try:
    ssid = data.get('SSID')
    config.remove_network(ssid)
    with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
      response.send("OK")
  except Exception as e:
    print("Could not parse data, or save file ")
    print(e)
    with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
      response.send(f"Could not parse data, or save file\n{str(e)}")

if wifi_connected and my_ip != None:
  #Start the server.
  print(f"Listening on http://{my_ip}:80")
  server.start(str(my_ip))

loop_times = [] #TODO just for testing
while True:
  #start_ms = int(time.time() * 1000)
  if initialised:
    node_process.receive_message()
    node_process.tick()
  try:
    server.poll()
  except OSError as error:
    print(error)
    continue
  """ end_ms = int(time.time() * 1000)
  loop_times.append(end_ms - start_ms)
  if len(loop_times) > 50:
    print("Average loop time: " + str(sum(loop_times) / len(loop_times)))
    loop_times = [] """