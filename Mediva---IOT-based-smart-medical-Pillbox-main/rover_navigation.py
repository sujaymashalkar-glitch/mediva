from machine import Pin, PWM, time_pulse_us
from micropython import const
import bluetooth
import network
import time

# =====================================================
# ================= CONFIG =============================
# =====================================================

FREE_DISTANCE = 30.0
SENSOR_TIMEOUT_US = 35000

RSSI_CLOSE = -55
RSSI_MID   = -70
RSSI_BUF   = 5

SERVO_FREQ = 50
MOTOR_FREQ = 1000

TURN_TIME = 0.55
REVERSE_TIME = 0.6
STRAIGHT_BURST = 0.4

ANGLE_CENTER = 90
ANGLE_LEFT   = 30
ANGLE_RIGHT  = 150

MOTOR_SPEED = 700

# ---------- ARRIVAL DETECTION ----------
ARRIVAL_RSSI = RSSI_CLOSE     # -55
ARRIVAL_TIME = 5              # seconds RSSI must stay strong
RSSI_CHECK_INTERVAL = 0.2

# =====================================================
# ================= PINS ===============================
# =====================================================

TRIG_PIN = 2
ECHO_PIN = 15
SERVO_PIN = 23

ENA_PIN = 18
ENB_PIN = 19
IN1_PIN = 5
IN2_PIN = 17
IN3_PIN = 16
IN4_PIN = 4

# =====================================================
# ================= HARDWARE SETUP =====================
# =====================================================

trig = Pin(TRIG_PIN, Pin.OUT)
echo = Pin(ECHO_PIN, Pin.IN)

servo = PWM(Pin(SERVO_PIN), freq=SERVO_FREQ)

ENA = PWM(Pin(ENA_PIN), freq=MOTOR_FREQ)
ENB = PWM(Pin(ENB_PIN), freq=MOTOR_FREQ)
IN1 = Pin(IN1_PIN, Pin.OUT)
IN2 = Pin(IN2_PIN, Pin.OUT)
IN3 = Pin(IN3_PIN, Pin.OUT)
IN4 = Pin(IN4_PIN, Pin.OUT)

ENA.duty(MOTOR_SPEED)
ENB.duty(MOTOR_SPEED)

# =====================================================
# ================= BLE SETUP ==========================
# =====================================================

_IRQ_CENTRAL_CONNECT    = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)

UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
RX_UUID   = bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")
UART_SERVICE = (UART_UUID, ((RX_UUID, bluetooth.FLAG_WRITE),),)

ble = bluetooth.BLE()
ble.active(True)
((rx_handle,),) = ble.gatts_register_services((UART_SERVICE,))

conn_handle = None
last_ble_rssi = None

def ble_irq(event, data):
    global conn_handle
    if event == _IRQ_CENTRAL_CONNECT:
        conn_handle, _, _ = data
        print("✅ BLE connected")
    elif event == _IRQ_CENTRAL_DISCONNECT:
        conn_handle = None
        advertise()
        print("❌ BLE disconnected")

ble.irq(ble_irq)

def advertise():
    name = b"Mediva"
    adv = b'\x02\x01\x02' + bytes((len(name)+1, 0x09)) + name
    ble.gap_advertise(100, adv)

advertise()

# =====================================================
# ================= WIFI ===============================
# =====================================================

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect("RONAK", "12345678")

while not wifi.isconnected():
    time.sleep(0.3)

def wifi_rssi():
    try:
        return wifi.status('rssi')
    except:
        return -100

# =====================================================
# ================= RSSI FILTER ========================
# =====================================================

rssi_buf = []

def get_rssi():
    global last_ble_rssi

    try:
        if conn_handle:
            r = ble.gap_rssi(conn_handle)
            last_ble_rssi = r
        else:
            r = wifi_rssi()
    except:
        r = -100

    rssi_buf.append(r)
    if len(rssi_buf) > RSSI_BUF:
        rssi_buf.pop(0)

    return sum(rssi_buf) / len(rssi_buf)

# =====================================================
# ================= UTILITIES ==========================
# =====================================================

def set_servo_angle(angle):
    duty = int(40 + (angle / 180.0) * 75)
    servo.duty(duty)
    time.sleep_ms(200)

def get_distance_cm():
    trig.off()
    time.sleep_us(2)
    trig.on()
    time.sleep_us(10)
    trig.off()
    try:
        t = time_pulse_us(echo, 1, SENSOR_TIMEOUT_US)
        if t <= 0:
            return -1
        return (t * 0.0343) / 2
    except:
        return -1

def is_clear(d):
    return d > FREE_DISTANCE

# =====================================================
# ================= MOTOR CONTROL ======================
# =====================================================

def stop_motors():
    IN1.off(); IN2.off(); IN3.off(); IN4.off()

def forward():
    IN1.on(); IN2.off()
    IN3.on(); IN4.off()

def reverse():
    IN1.off(); IN2.on()
    IN3.off(); IN4.on()

def turn_left_inplace():
    IN1.off(); IN2.on()
    IN3.on();  IN4.off()

def turn_right_inplace():
    IN1.on();  IN2.off()
    IN3.off(); IN4.on()

def small_forward_burst():
    forward()
    time.sleep(STRAIGHT_BURST)
    stop_motors()

# =====================================================
# ================= RSSI STEERING =====================
# =====================================================

def rssi_steer():
    rssi = get_rssi()
    if rssi >= RSSI_CLOSE:
        return "STRAIGHT"
    elif RSSI_MID <= rssi < RSSI_CLOSE:
        return "LEFT"
    else:
        return "RIGHT"

# =====================================================
# ================= ARRIVAL CHECK =====================
# =====================================================

def reached_patient():
    stable_start = None

    while True:
        rssi = get_rssi()

        if rssi >= ARRIVAL_RSSI:
            if stable_start is None:
                stable_start = time.time()
            elif time.time() - stable_start >= ARRIVAL_TIME:
                print("📍 Patient reached (RSSI stable)")
                return True
        else:
            stable_start = None

        time.sleep(RSSI_CHECK_INTERVAL)

# =====================================================
# ================= NAVIGATION =========================
# =====================================================

def navigate_to_patient():
    print("🚀 Navigation started")
    set_servo_angle(ANGLE_CENTER)

    while True:

        # ---- ARRIVAL DETECTION ----
        if reached_patient():
            stop_motors()
            return

        set_servo_angle(ANGLE_CENTER)
        d = get_distance_cm()

        if is_clear(d):
            decision = rssi_steer()
            if decision == "STRAIGHT":
                forward()
            elif decision == "LEFT":
                turn_left_inplace()
                time.sleep(0.2)
            else:
                turn_right_inplace()
                time.sleep(0.2)
            time.sleep(0.1)
            continue

        stop_motors()
        time.sleep(0.1)

        set_servo_angle(ANGLE_LEFT)
        if is_clear(get_distance_cm()):
            turn_left_inplace()
            time.sleep(TURN_TIME)
            stop_motors()
            small_forward_burst()
            continue

        set_servo_angle(ANGLE_RIGHT)
        if is_clear(get_distance_cm()):
            turn_right_inplace()
            time.sleep(TURN_TIME)
            stop_motors()
            small_forward_burst()
            continue

        reverse()
        time.sleep(REVERSE_TIME)
        stop_motors()

# =====================================================
# ================= PUBLIC API =========================
# =====================================================

def start_navigation():
    stop_motors()
    set_servo_angle(ANGLE_CENTER)
    navigate_to_patient()

def stop_navigation():
    stop_motors()
    set_servo_angle(ANGLE_CENTER)
