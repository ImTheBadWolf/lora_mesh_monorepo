import time
import board
import busio
import terminalio
import displayio
import gc
import os
import microcontroller
from adafruit_simple_text_display import SimpleTextDisplay

from adafruit_st7789 import ST7789

exec(open("main.py").read())
print("Program finished ... rebooting ....")
microcontroller.reset()
