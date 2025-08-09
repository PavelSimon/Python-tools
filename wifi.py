import platform
import re
import subprocess


def get_wifi_passwords() -> None:
    """Retrieve and display stored Wi-Fi passwords using ``netsh``."""

    try:
        data = subprocess.check_output(
            ["netsh", "wlan", "show", "profiles"],
            stderr=subprocess.STDOUT,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Failed to list profiles: {e.output.strip()}")
        return

    profiles = re.findall(r"All User Profile\s*:\s(.*)", data)
    for profile in profiles:
        profile_name = profile.strip()

        if not re.fullmatch(r"[\w\- ]+", profile_name):
            print(f"Skipping suspicious profile name: {profile_name!r}")
            continue

        try:
            info = subprocess.check_output(
                ["netsh", "wlan", "show", "profile", profile_name, "key=clear"],
                stderr=subprocess.STDOUT,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"Failed to get profile {profile_name}: {e.output.strip()}")
            continue

        password = re.search(r"Key Content\s*:\s(.*)", info)
        if password:
            print(f"{profile_name}: {password.group(1)}")


def main() -> None:
    if platform.system().lower() != "windows":
        print("This script only runs on Windows.")
        return

    get_wifi_passwords()


if __name__ == "__main__":
    main()
