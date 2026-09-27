from machine import I2C, Pin
import ds3231
import time

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
rtc = ds3231.DS3231(i2c)

# SET TIME ONCE (change values)
rtc.set_datetime(2026, 1, 25, 5, 12, 40, 0)

while True:
    print(rtc.datetime())
    time.sleep(1)
