# ===================== IMPORTS =====================
from machine import Pin, SPI, I2C
import time
import gc9a01
import network
import urequests
from truetype import NotoSerif_32 as FONT
from max30102 import MAX30102
import ds3231

# ===================== THINGSPEAK =====================
THINGSPEAK_WRITE_API = "78S00I8D5198MEEY"
THINGSPEAK_URL = "https://api.thingspeak.com/update"

# ===================== WIFI =====================
SSID = "SUJAY"
PASSWORD = "12345678"

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
if not wifi.isconnected():
    wifi.connect(SSID, PASSWORD)
    while not wifi.isconnected():
        time.sleep_ms(500)

print("WiFi connected")

# ===================== RTC =====================
rtc_i2c = I2C(0, scl=Pin(7), sda=Pin(6))
rtc = ds3231.DS3231(rtc_i2c)

# ===================== MEASUREMENT SCHEDULE =====================
MORNING_TIME   = "09:00"
AFTERNOON_TIME = "14:00"
NIGHT_TIME     = "20:00"

last_minute = -1
morning_done = False
afternoon_done = False
night_done = False

# ===================== DISPLAY =====================
backlight = Pin(2, Pin.OUT)

tft = gc9a01.GC9A01(
    SPI(2, baudrate=80000000, polarity=0, sck=Pin(10), mosi=Pin(11)),
    240, 240,
    reset=Pin(14, Pin.OUT),
    cs=Pin(9, Pin.OUT),
    dc=Pin(8, Pin.OUT),
    backlight=backlight,
    rotation=0,
    buffer_size=16 * 32 * 2
)
tft.init()
tft.fill(gc9a01.BLACK)

BLACK = gc9a01.BLACK
WHITE = gc9a01.WHITE
CYAN  = gc9a01.CYAN
GREEN = gc9a01.GREEN

def center(text, y, color):
    w = tft.write_len(FONT, text)
    tft.write(FONT, text, 120 - w // 2, y, color)

# ===================== TOUCH =====================
touch_i2c = I2C(1, scl=Pin(18), sda=Pin(17), freq=400000)

def touched():
    try:
        return touch_i2c.readfrom_mem(0x15, 0x02, 1)[0] & 0x0F
    except:
        return 0

# ===================== MAX30102 =====================
sensor = MAX30102(touch_i2c)
sensor.i2c.writeto_mem(0x57, 0x0C, b'\x00')
sensor.i2c.writeto_mem(0x57, 0x0D, b'\x00')

# ===================== HEALTH DATA =====================
bpm = 0
spo2 = 0
measuring = False
health_done = False

# ===================== SEND TO THINGSPEAK =====================
def send_health_to_cloud(bpm, spo2):
    url = f"{THINGSPEAK_URL}?api_key={THINGSPEAK_WRITE_API}&field7={bpm}&field8={spo2}"
    try:
        r = urequests.get(url)
        r.close()
        print("📡 Health data sent")
    except:
        print("❌ ThingSpeak error")

# ===================== MEASURE HEALTH =====================
def measure_health():
    global bpm, spo2, measuring
    measuring = True
    backlight.off()

    start = time.ticks_ms()
    beats = []
    ir_avg = 0
    last_beat = 0
    red_sum = ir_sum = samples = 0

    while time.ticks_diff(time.ticks_ms(), start) < 15000:
        red, ir = sensor.read_fifo()
        ir_avg = int(0.95 * ir_avg + 0.05 * ir)
        now = time.ticks_ms()

        if ir > ir_avg + 3000 and now - last_beat > 450:
            beats.append(now)
            last_beat = now

        red_sum += red
        ir_sum += ir
        samples += 1
        time.sleep_ms(30)

    bpm = int(60000 / ((beats[-1] - beats[0]) / (len(beats) - 1))) if len(beats) >= 3 else 0
    spo2 = int(110 - 25 * ((red_sum / samples) / (ir_sum / samples))) if samples else 0

    if bpm > 0 and spo2 > 0:
        send_health_to_cloud(bpm, spo2)

    backlight.on()
    measuring = False

# ===================== TIME CHECK =====================
def check_health_time():
    global last_minute, morning_done, afternoon_done, night_done

    now = rtc.datetime()
    hour, minute = now[4], now[5]
    current = f"{hour:02d}:{minute:02d}"

    if minute != last_minute:
        morning_done = afternoon_done = night_done = False
        last_minute = minute

    if current == MORNING_TIME and not morning_done:
        morning_done = True
        return True
    if current == AFTERNOON_TIME and not afternoon_done:
        afternoon_done = True
        return True
    if current == NIGHT_TIME and not night_done:
        night_done = True
        return True
    return False

# ===================== UI =====================
def draw_home():
    tft.fill(BLACK)
    center("MEDIVA", 40, WHITE)
    center("Tap for Health", 120, CYAN)

draw_home()

# ===================== MAIN LOOP =====================
while True:
    if check_health_time() and not measuring:
        measure_health()
        draw_home()

    if touched() and not measuring:
        measure_health()
        draw_home()

    time.sleep_ms(200)
