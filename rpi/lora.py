#sx1276
#rfm96
#loraspi v1.2
from raspi_lora import LoRa, ModemConfig
import RPi.GPIO as GPIO
import time
""" Raspberry PI   RFM9x Module 1
GPIO22 < --- -> Reset
GPIO25 < --- -> DIO0 OR DIO1 OR DIO2(Hardware OR done with 1N4148 Diode and R3)

Raspberry PI   On Board LEDS
GPIO23 < --- -> LED D3 TX/RX
GPIO24 < --- -> LED D4 LED

pip install --upgrade pyLoraRFM9x
 """

#from pyLoraRFM9x import LoRa, ModemConfig


def on_recv(payload):
    print("From:", payload.header_from)
    print("Received:", payload.message)
    print("RSSI: {}; SNR: {}".format(payload.rssi, payload.snr))


GPIO.setwarnings(False)

lora = LoRa(0, 25, 2, modem_config=ModemConfig.Bw500Cr45Sf128, freq=868, tx_power=14, acks=True, receive_all=True)
lora.on_recv = on_recv


print("Lora initialized")
lora.send_armachat("rpi")

while(True):
  pass
