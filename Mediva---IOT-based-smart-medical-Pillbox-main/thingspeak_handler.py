from machine import I2C, Pin
import network
import urequests
import time
import ds3231

# =====================================================
# WIFI
# =====================================================
wifi = network.WLAN(network.STA_IF)
wifi.active(True)

if not wifi.isconnected():
    print("📶 Connecting to WiFi...")
    wifi.connect("SUJAY", "12345678")
    while not wifi.isconnected():
        time.sleep(1)

print("✅ WiFi connected")

# =====================================================
# THINGSPEAK CONFIG
# =====================================================
CHANNEL_ID = "3232963"
READ_API  = "OVJOWI2UVIEUY08V"
WRITE_API = "78S00I8D5198MEEY"

READ_URL = (
    f"https://api.thingspeak.com/channels/"
    f"{CHANNEL_ID}/feeds/last.json?api_key={READ_API}"
)
WRITE_URL = f"https://api.thingspeak.com/update?api_key={WRITE_API}"

# =====================================================
# RTC
# =====================================================
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
rtc = ds3231.DS3231(i2c)

# =====================================================
# INTERNAL STATE
# =====================================================
last_minute = -1
morning_done = False
afternoon_done = False
night_done = False

# =====================================================
# CHECK ALARM
# =====================================================
def check_alarm():
    global last_minute, morning_done, afternoon_done, night_done

    try:
        data = urequests.get(READ_URL).json()
        m_time = str(data.get("field1")).strip()[:5]
        a_time = str(data.get("field2")).strip()[:5]
        n_time = str(data.get("field3")).strip()[:5]
    except:
        return None

    now = rtc.datetime()
    hour = now[4]
    minute = now[5]
    current_time = f"{hour:02d}:{minute:02d}"

    # Reset flags every new minute
    if minute != last_minute:
        morning_done = False
        afternoon_done = False
        night_done = False
        last_minute = minute

    if current_time == m_time and not morning_done:
        morning_done = True
        return "morning"

    if current_time == a_time and not afternoon_done:
        afternoon_done = True
        return "afternoon"

    if current_time == n_time and not night_done:
        night_done = True
        return "night"

    return None

# =====================================================
# UPDATE STATUS
# =====================================================
def update_status(slot, value):
    field_map = {
        "morning": "field4",
        "afternoon": "field5",
        "night": "field6"
    }

    field = field_map.get(slot)
    if not field:
        return

    try:
        urequests.get(f"{WRITE_URL}&{field}={value}")
    except:
        pass
