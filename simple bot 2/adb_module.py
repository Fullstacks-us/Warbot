import subprocess
import logging

class ADBModule:
    def __init__(self):
        self.logger = logging.getLogger("ADBModule")
        self.device_id = self.get_device_id()

    def execute_adb_command(self, command_list):
        """Execute an ADB command."""
        cmd_str = " ".join(command_list)
        result = subprocess.run(command_list, capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else None

    def get_device_id(self):
        """Retrieve the first available ADB device."""
        devices_output = self.execute_adb_command(["adb", "devices"])

        if not devices_output:
            self.logger.error("❌ No ADB devices found. Ensure your device/emulator is connected.")
            return None

        lines = devices_output.split("\n")
        device_list = [line.split("\t")[0] for line in lines[1:] if "device" in line]

        if device_list:
            self.logger.info(f"✅ Using ADB device: {device_list[0]}")
            return device_list[0]
        else:
            self.logger.error("❌ No connected ADB devices.")
            return None

    def tap_screen(self, x, y):
        """Tap a location on the screen."""
        if self.device_id:
            self.execute_adb_command(["adb", "-s", self.device_id, "shell", "input", "tap", str(x), str(y)])
        else:
            self.logger.error("❌ No device connected. Cannot tap screen.")

    def capture_screenshot(self, local_path):
        """Capture and pull a screenshot."""
        if self.device_id:
            self.execute_adb_command(["adb", "-s", self.device_id, "shell", "screencap", "-p", "/sdcard/temp.png"])
            self.execute_adb_command(["adb", "-s", self.device_id, "pull", "/sdcard/temp.png", local_path])
            return True
        else:
            self.logger.error("❌ No device connected. Cannot capture screenshot.")
            return False

    def press_escape(self):
        """Press the ESC key (Keycode 111) to close pop-ups."""
        if self.device_id:
            self.execute_adb_command(["adb", "-s", self.device_id, "shell", "input", "keyevent", "111"])
        else:
            self.logger.error("❌ No device connected. Cannot send ESC key event.")
