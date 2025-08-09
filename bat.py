import os
import time

import psutil

if os.name == "nt":
    import msvcrt
else:
    import keyboard


def battery_alert():
    print("Press ESC to stop monitoring...")
    while True:
        if os.name == "nt":
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b"\x1b":
                    print("\nStopping battery monitor...")
                    break
        else:
            if keyboard.is_pressed("esc"):
                print("\nStopping battery monitor...")
                break
        battery = psutil.sensors_battery()
        if battery is None:
            print("No battery information available.")
            break
        print(f"🔋 Battery: {battery.percent}%")
        if battery.percent < 15 and not battery.power_plugged:
            print("⚠️  Battery low! Plug in the charger.")
        time.sleep(1)


if __name__ == "__main__":
    battery_alert()
