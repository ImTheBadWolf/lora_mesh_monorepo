import board
import busio
import digitalio
import sys
import digitalio
import board
import busio
import spidev

sys.path.append("custom_protocol_lib")
import protocol_config
from base_utils import *
from node_process import *
import rfm9x_lora


config = protocol_config.ProtocolConfig('data/settings.json')
initialised = config.is_initialised()

if not initialised:
  print("My address not set. Please edit data/settings.json and set MY_ADDRESS")
  sys.exit()

message_to_send = f'Hello world from 0x{config.MY_ADDRESS:04X}'

def show_info_notification(text):
  if config.DEBUG:
    print(text)

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

symbolDuration = 1000 / ( rfm9x.signal_bandwidth / (1 << rfm9x.spreading_factor) )
if symbolDuration > 16:
    rfm9x.low_datarate_optimize = 1
    print("low datarate on")
else:
    rfm9x.low_datarate_optimize = 0
    print("low datarate off")

node_process = NodeProcess(rfm9x, show_info_notification, config)

while True:

    node_process.tick()
    r_msg = node_process.get_latest_message()

    if r_msg is not None:
      (msg_instance, snr, rssi) = r_msg
      print(f'Received SNR:{snr} RSSI:{rssi}')

      if msg_instance.get_message_type() == MessageType.SENSOR_DATA:
        print(f'From: 0x{msg_instance.get_sender():04x}, ttl: {msg_instance.get_ttl()}')
        print(f'{msg_instance.get_sensor_data().decode("utf-8")}')
      else:
        print(f'From: 0x{msg_instance.get_sender():04x}, maxhop: {msg_instance.get_maxHop()}')
        print(f'{msg_instance.get_text_message().decode("utf-8")}')
        print(f'Initial maxhop:{msg_instance.get_initialMaxHop()}')
      print(f'Msg ID:{msg_instance.get_message_id()}')