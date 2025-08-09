import subprocess
import re

def get_wifi_passwords():
    data = subprocess.check_output('netsh wlan show profiles', shell=True)
    profiles = re.findall("All User Profile\s*:\s(.*)", data.decode())
    for profile in profiles:
        info = subprocess.check_output(f'netsh wlan show profile "{profile.strip()}" key=clear', shell=True)
        password = re.search("Key Content\s*:\s(.*)", info.decode())
        if password:
            print(f"{profile.strip()}: {password.group(1)}")

get_wifi_passwords()
