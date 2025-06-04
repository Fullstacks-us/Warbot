# adb_module.py
import subprocess
import logging
import os

class ADBModule:
    def __init__(self):
        self.logger = logging.getLogger("ADBModule")
        self._setup_logging()
        self.device_id = self.get_device_id()

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

    def get_device_id(self):
        """Retrieve the first available ADB device ID dynamically."""
        self.logger.warning("🔍 Checking for connected ADB devices...")
        devices_output = self.execute_adb_command(["adb", "devices"])
        if not devices_output:
            self.logger.error("❌ Could not retrieve ADB devices list.")
            return None

        devices = devices_output.split("\n")[1:]
        device_list = [line.split("\t")[0] for line in devices if "device" in line]

        if device_list:
            self.logger.warning(f"✅ Using ADB device: {device_list[0]}")
            return device_list[0]
        else:
            self.logger.error("❌ No ADB device found. Ensure your device is connected.")
            return None

    def capture_screenshot(self, local_path):
        """
        Captures a screenshot on the device and pulls it to `local_path`.
        """
        if not self.device_id:
            self.logger.error("❌ No valid ADB device found. Cannot take a screenshot.")
            return False

        base_name = os.path.basename(local_path)
        # 1. Capture to /sdcard
        capture_cmd = ["adb", "-s", self.device_id, "shell", "screencap", "-p", f"/sdcard/{base_name}"]
        pull_cmd = ["adb", "-s", self.device_id, "pull", f"/sdcard/{base_name}", local_path]

        self.execute_adb_command(capture_cmd)
        self.execute_adb_command(pull_cmd)
        self.logger.info(f"[{self.device_id}] Screenshot saved to {local_path}")
        return True

    def tap_screen(self, x, y):
        """Sends an ADB tap command to the device at (x, y)."""
        if not self.device_id:
            self.logger.error("❌ No valid ADB device found. Cannot tap screen.")
            return
        tap_cmd = ["adb", "-s", self.device_id, "shell", "input", "tap", str(x), str(y)]
        self.execute_adb_command(tap_cmd)
        self.logger.info(f"[{self.device_id}] Tapped at ({x}, {y})")

    def press_escape(self):
        """Sends an ESC (KEYCODE_ESCAPE = 111) keyevent to the device/emulator."""
        if not self.device_id:
            self.logger.error("❌ No valid ADB device found. Cannot press ESC.")
            return
        esc_cmd = ["adb", "-s", self.device_id, "shell", "input", "keyevent", "111"]
        self.execute_adb_command(esc_cmd)
        self.logger.info(f"[{self.device_id}] Pressed ESC (keycode 111)")
