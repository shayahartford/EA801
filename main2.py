from machine import Pin, SoftI2C
from ssd1306 import SSD1306_I2C

i2c = SoftI2C(scl=Pin(3), sda=Pin(2), freq=400000)
oled = SSD1306_I2C(128, 64, i2c, addr=0x3C)

oled.fill(0)
oled.text("Horario", 30, 28)
oled.show()
