import os
from time import sleep
import board
import digitalio
import gc
import json
import sys
from flask import Flask, json, render_template, send_from_directory, request
import threading

sys.path.append("custom_protocol_lib")
import protocol_config
from base_utils import *
from node_process import NodeProcess
from address_book import AddressBook
import rfm9x_lora
import spidev

config = protocol_config.ProtocolConfig('data/settings.json')
initialised = config.is_initialised()


spi_lora = spidev.SpiDev()
spi_lora.open(0, 0)
spi_lora.max_speed_hz = 500000

RESET = digitalio.DigitalInOut(board.D22)


rfm9x = rfm9x_lora.RFM9x(spi_lora, 868.0, crc=True)
lora_config = config.LORA_CONFIG
rfm9x.signal_bandwidth = lora_config[0] * 1000
rfm9x.coding_rate = lora_config[1]
rfm9x.spreading_factor = lora_config[2]

rfm9x.tx_power = 23
rfm9x.preamble_length = 8

def show_info_notification(text):
  if config.DEBUG:
    print(text)

symbolDuration = 1000 / ( rfm9x.signal_bandwidth / (1 << rfm9x.spreading_factor) )
if symbolDuration > 16:
    rfm9x.low_datarate_optimize = 1
    if config.DEBUG:
      print("low datarate on")
else:
    rfm9x.low_datarate_optimize = 0
    if config.DEBUG:
      print("low datarate off")

if initialised:
  node_process = NodeProcess(rfm9x, show_info_notification, config, queue_hard_limit=1000)
  address_book = AddressBook("data/contacts.json", "data/sensors.json")
  try:
    address_book.add_contact("YOU", f"0x{config.MY_ADDRESS:04X}")
    address_book.add_contact("ALL", f"0x{config.BROADCAST_ADDRESS:04X}")
    address_book.add_sensor("YOU", f"0x{config.MY_ADDRESS:04X}")
    address_book.add_sensor("ALL", f"0x{config.BROADCAST_ADDRESS:04X}")
  except:
    pass

else:
  print("Not initialised, set your address first. Then restart the device.")

server = Flask(__name__, static_url_path='/web', static_folder='web')

@server.route("/")
def base():
  if not initialised:
    return send_from_directory('web', 'config.html')
  else:
    return send_from_directory('web', 'index.html')

@server.route("/sensors")
def sensors_route():
  if not initialised:
    return send_from_directory('web', 'config.html')
  else:
    return send_from_directory('web', 'sensors.html')

@server.route("/contacts")
def contacts_route():
  if not initialised:
    return send_from_directory('web', 'config.html')
  else:
    return send_from_directory('web', 'contacts.html')

@server.route("/config")
def config_route():
  return send_from_directory('web', 'config.html')

#List messages
@server.route("/api/messages")
def api_messages():
  if initialised:
    messages = node_process.get_user_messages()
    parsed_messages = parse_messages(messages, config)
    gc.collect()

    try:
      page = request.args.get('page', default = 0, type = int)
      page = int(page)
    except:
      page = 0

    page_size = 20
    num_pages = (len(parsed_messages)-1) // page_size + 1

    data = {
      'messages': parsed_messages[page*page_size:(page+1)*page_size],
      'pages': num_pages,
      'total': len(parsed_messages),
    }

    try:
      return json.dumps(data)
    except MemoryError as e:
      print(e)
      if config.DEBUG:
        print(f"Free memory: {gc.mem_free()} page: {page} len: {len(data['messages'])}")
        print(f"Allocated memory: {gc.mem_alloc()}")

#Create and send new text message
@server.route("/api/send_text_message", methods=['POST'])
def api_send_message():
  if initialised:
    try:
      data = request.json
      destination = int(data.get('destination'), 16)
      message = data.get('message')
      message = message[:238] #Limit message length to 238 characters
      max_hop = int(data.get('max_hop'))
      priority = int(data.get('priority'))
      w_ack = data.get('wack')
      node_process.new_text_message(destination, message, w_ack, max_hop, priority)
      gc.collect()
      return "OK"
    except Exception as e:
      if config.DEBUG:
        print("Could not parse data")
      print(e)
      return "Error" + e

#Resend message
@server.route("/api/resend_message", methods=['POST'])
def api_resend_message():
  if initialised:
    try:
      data = request.json
      message_id = int(data.get('message_id'))
      node_process.resend_text_message(message_id)
      gc.collect()
      return("OK")
    except:
      if config.DEBUG:
        print("Could not parse data")
      return("Could not parse data")

@server.route("/api/contacts")
def api_contacts():
  if initialised:
    contacts = address_book.get_contacts()

    data = {
      'contacts': contacts
    }
  return(json.dumps(data))

@server.route("/api/contact", methods=['PUT'])
def api_add_contact():
  if initialised:
    try:
      data = request.json
      address = data.get('address')
      name = data.get('name')
      address_book.add_contact(name, address)
      return("OK")
    except:
      if config.DEBUG:
        print("Could not parse data, or save file")
      return("Could not parse data, or save file")

@server.route("/api/contact", methods=['DELETE'])
def api_del_contact():
  if initialised:
    try:
      data = request.json
      address = data.get('address')
      address_book.del_contact(address)
      return("OK")
    except:
      if config.DEBUG:
        print("Could not parse data, or save file")
      return("Could not parse data, or save file")

@server.route("/api/sensors")
def api_sensors():
  if initialised:
    sensors = address_book.get_sensors()

    data = {
      'sensors': sensors
    }
    return(json.dumps(data))

@server.route("/api/sensor", methods=['PUT'])
def api_add_sensor():
  if initialised:
    try:
      data = request.json
      address = data.get('address')
      name = data.get('name')
      address_book.add_sensor(name, address)
      return("OK")
    except Exception as e:
      if config.DEBUG:
        print("Could not parse data, or save file")
      print(e)
      return("Could not parse data, or save file" + e)

@server.route("/api/sensor", methods=['DELETE'])
def api_del_sensor():
  if initialised:
    try:
      data = request.json
      address = data.get('address')
      address_book.del_sensor(address)
      return("OK")
    except:
      if config.DEBUG:
        print("Could not parse data, or save file")
      return("Could not parse data, or save file")

#Create and send new traceroute request
@server.route("/api/traceroute", methods=['POST'])
def api_send_traceroute():
  if initialised:
    try:
      data = request.json
      destination = int(data.get('destination'), 16)
      max_hop = int(data.get('max_hop'))
      priority = int(data.get('priority'))
      node_process.new_traceroute_request(destination, max_hop, priority)
      gc.collect()
      return("OK")
    except:
      if config.DEBUG:
        print("Could not parse data")
      return("Could not parse data")

#Dump message queue
@server.route("/api/dump")
def api_dump():
  if initialised:
    message_queue = node_process.get_message_queue()
    parsed_message_queue = parse_message_queue(message_queue)
    gc.collect()

    try:
      page = request.args.get('page', default = 0, type = int)
      page = int(page)
    except:
      page = 0

    page_size = 20
    num_pages = (len(parsed_message_queue)-1) // page_size + 1
    received, sent = node_process.get_stats()

    data = {
      'messages': parsed_message_queue[page*page_size:(page+1)*page_size],
      'device_info': {
        'received': received,
        'sent': sent
      },
      'pages': num_pages,
      'total': len(parsed_message_queue),
    }
    try:
      return(json.dumps(data))
    except MemoryError as e:
      print(e)
      if config.DEBUG:
        print(f"Free memory: {gc.mem_free()} page: {page} len: {len(data['messages'])}")
        print(f"Allocated memory: {gc.mem_alloc()}")

@server.route("/api/config")
def api_config():
  data = {
    'config': config.get_config(),
  }
  return(json.dumps(data))

@server.route("/api/clear")
def delete_queue():
  node_process.delete_queue()
  return("OK")

@server.route("/api/config", methods=['PUT'])
def api_update_config():
  data = request.json
  try:
    new_config = data.get('config')
    config.update_config(new_config)
    if config.is_reboot_required():
      print("Restarting")
      sleep(1)
      os.execl(sys.executable, sys.executable, *sys.argv)
    return("OK")
  except Exception as e:
    if config.DEBUG:
      print("Could not parse data, or save file ")
    print(e)
    return(f"Could not parse data, or save file\n{str(e)}")

def process_loop(node_process):
  while True:
    try:
      if initialised:
        node_process.tick()
    except Exception as e:
      print(e)

if __name__ == '__main__':
  t = threading.Thread(target=process_loop, args=(node_process,))
  t.start()
  server.run(host='0.0.0.0', port=8080)