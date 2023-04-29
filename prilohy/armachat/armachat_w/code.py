import time
import board
import busio
import terminalio
import displayio
import gc
import os
import microcontroller
import storage
import displayio
from config import config
from adafruit_simple_text_display import SimpleTextDisplay
import adafruit_matrixkeypad
from adafruit_st7789 import ST7789
""" 
# Release any resources currently in use for the displays
displayio.release_displays()

tft_cs = board.GP21
tft_dc = board.GP16

spi_mosi = board.GP19
spi_clk = board.GP18
spi = busio.SPI(spi_clk, spi_mosi)
backlight = board.GP20

display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs)

display = ST7789(
    display_bus, rotation=270, width=320, height=240, backlight_pin=backlight
) """

# Make the display context
# splash = displayio.Group()
# display.show(splash)

""" print("Free memory:")
print(gc.mem_free())
print("Hold alt for write mode toggle")
writemode = True #When true, the drive is writable by USB, else it is read only for USB(PC) but can be written to from circuitpython
keypad = adafruit_matrixkeypad.Matrix_Keypad(config.rows, config.cols, config.keys1)
for x in range(16):
    s = "["
    for i in range(0, 16):
        if 15 - i > x:
            s = s + "-"
        else:
            s = s + " "
    if x == 15:
        print(s + "]\n")
    else:
        print(s + "]\r", end='')

    time.sleep(0.05)
    keys = keypad.pressed_keys

    if not keys:
        continue
    if keys[0] == "bsp":
        print("SAFE MODE DETECTED .....")
        microcontroller.on_next_reset(microcontroller.RunMode.SAFE_MODE)
        microcontroller.reset()
    if keys[0] == "alt":
        print("Write mode enabled .....")
        writemode = False """

# RENAME DRIVE
new_name = "ARMACHAT05"

""" storage.remount("/", readonly=False)
m = storage.getmount("/")
m.label = new_name
storage.remount("/", readonly=writemode) """


program_name = 'main-web.py'
print("Starting: " + program_name)
exec(open(program_name).read())
print("Program finished ... rebooting ....")
microcontroller.reset()
