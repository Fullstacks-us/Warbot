import subprocess
import logging
import os

class ADBModule:
    def __init__(self):
        self.logger = logging.getLogger("ADBModule")
        self._setup_logging()

    def _setup_logging(self):
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def execute_adb_command(self, command_list):
        """Execute an ADB command synchronously, capturing output."""
        try:
            cmd_str = " ".join(command_list)
            self.logger.info(f"Executing command: {cmd_str}")
            result = subprocess.run(command_list, capture_output=True, text=True)
            if result.returncode == 0:
                self.logger.info(f"Command executed successfully: {cmd_str}")
                return result.stdout
            else:
                self.logger.error(f"Command failed: {cmd_str}\nError: {result.stderr}")
                return None
        except Exception as e:
            self.logger.error(f"Failed to execute command: {command_list}\nError: {e}")
            return None

    def capture_screenshot(self, device_id, local_path):
        """
        Captures a screenshot on the device and pulls it to `local_path`.
        """
        base_name = os.path.basename(local_path)
        # 1. Capture to /sdcard
        self.execute_adb_command(["adb", "-s", device_id, "shell", "screencap", "-p", f"/sdcard/{base_name}"])
        # 2. Pull to local
        self.execute_adb_command(["adb", "-s", device_id, "pull", f"/sdcard/{base_name}", local_path])
        self.logger.info(f"[{device_id}] Screenshot saved to {local_path}")

    def tap_screen(self, device_id, x, y):
        """Sends an ADB tap command to the device at (x, y)."""
        self.execute_adb_command(["adb", "-s", device_id, "shell", "input", "tap", str(x), str(y)])
        self.logger.info(f"[{device_id}] Tapped at ({x}, {y})")

    def press_escape(self, device_id):
        """Sends an ESC (KEYCODE_ESCAPE = 111) keyevent to the device/emulator."""
        self.execute_adb_command(["adb", "-s", device_id, "shell", "input", "keyevent", "111"])
        self.logger.info(f"[{device_id}] Pressed ESC (keycode 111)")
