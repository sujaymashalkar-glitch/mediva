from machine import Pin, PWM
import time

# =====================================================
# SERVO SETUP
# =====================================================
servo_m = PWM(Pin(13), freq=50)   # Morning
servo_a = PWM(Pin(12), freq=50)   # Afternoon
servo_n = PWM(Pin(14), freq=50)   # Night

CLOSED = 40
OPEN   = 120

def open_lid(servo):
    servo.duty(OPEN)

def close_lid(servo):
    servo.duty(CLOSED)

# Close all lids at boot
close_lid(servo_m)
close_lid(servo_a)
close_lid(servo_n)

# =====================================================
# LED SETUP
# =====================================================
led_m = Pin(25, Pin.OUT)
led_a = Pin(26, Pin.OUT)
led_n = Pin(27, Pin.OUT)

led_m.off()
led_a.off()
led_n.off()

# =====================================================
# BUZZER
# =====================================================
buzzer = Pin(33, Pin.OUT)
buzzer.off()

# =====================================================
# IR SENSORS
# =====================================================
ir_m = Pin(34, Pin.IN)
ir_a = Pin(35, Pin.IN)
ir_n = Pin(32, Pin.IN)

# =====================================================
# DISPENSE FUNCTION
# =====================================================
def dispense_medicine(slot, timeout=20):
    """
    slot: 'morning' | 'afternoon' | 'night'
    returns: 1 if medicine taken, 0 otherwise
    """

    if slot == "morning":
        servo, led, ir = servo_m, led_m, ir_m
    elif slot == "afternoon":
        servo, led, ir = servo_a, led_a, ir_a
    else:
        servo, led, ir = servo_n, led_n, ir_n

    print(f"💊 Dispensing {slot} medicine")

    led.on()
    buzzer.on()
    open_lid(servo)

    baseline = ir.value()
    start = time.time()

    while time.time() - start < timeout:
        if ir.value() != baseline:
            print("✅ Medicine taken")
            buzzer.off()
            led.off()
            close_lid(servo)
            return 1
        time.sleep(0.1)

    print("❌ Medicine NOT taken")
    buzzer.off()
    led.off()
    close_lid(servo)
    return 0
