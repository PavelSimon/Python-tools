import time
import pyperclip

history = []

def clipboard_logger():
    recent_value = ""
    while True:
        tmp_value = pyperclip.paste()
        if tmp_value != recent_value:
            recent_value = tmp_value
            history.append(recent_value)
            print(f"Copied: {recent_value}")
        time.sleep(1)

clipboard_logger()
