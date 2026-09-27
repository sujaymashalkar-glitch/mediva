import time
from thingspeak_handler import check_alarm, update_status
from compartment import dispense_medicine

print("💊 Smart Medication System Started")

while True:
    slot = check_alarm()

    if slot:
        print("⏰ Alarm:", slot)

        time.sleep(1)  # small visible delay
        taken = dispense_medicine(slot, timeout=20)
        update_status(slot, taken)

        time.sleep(5)  # cooldown

    time.sleep(0.5)
