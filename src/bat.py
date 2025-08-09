import psutil
import time
import sys
import msvcrt

def battery_alert():
    print("Press ESC to stop monitoring...")
    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b'\x1b':  # ESC key
                print("\nStopping battery monitor...")
                break
        battery = psutil.sensors_battery()
        print(f"🔋 Battery: {battery.percent}%")
        if battery.percent < 15 and not battery.power_plugged:
            print("⚠️  Battery low! Plug in the charger.")
        time.sleep(1)

battery_alert()
