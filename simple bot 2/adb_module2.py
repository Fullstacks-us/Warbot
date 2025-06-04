import subprocess
import logging
import shutil
import re
import os

class ADBModule:
    def __init__(self):
        self.logger = logging.getLogger("ADBModule")
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    def log_message(self, message, level=logging.INFO):
        """Log messages at the specified logging level."""
        self.logger.log(level, message)

    def check_adb_installed(self):
        """Check if the ADB tool is installed and accessible."""
        try:
            subprocess.run(["adb", "version"], capture_output=True, text=True, check=True)
            self.log_message("ADB tool is installed and accessible.")
        except FileNotFoundError:
            self.log_message("ADB tool is not installed or not in the PATH.", level=logging.ERROR)
            raise RuntimeError("ADB tool is not installed or not in the PATH.")
        except Exception as e:
            self.log_message(f"Error checking ADB installation: {e}", level=logging.ERROR)
            raise RuntimeError(f"Error checking ADB installation: {e}")

    def list_devices(self):
        """List all connected ADB devices."""
        try:
            self.check_adb_installed()
            result = subprocess.run(["adb", "devices"], capture_output=True, text=True, check=True)
            devices = result.stdout.strip().split("\n")[1:]  # Skip the header row
            connected_devices = [line.split("\t")[0] for line in devices if "device" in line]
            self.log_message(f"Connected devices: {connected_devices}")
            return connected_devices
        except Exception as e:
            self.log_message(f"Failed to list devices: {e}", level=logging.ERROR)
            raise RuntimeError(f"Failed to list devices: {e}")

    def validate_device_id(self, device_id):
        """Validate that the given device_id is in the list of connected devices."""
        connected_devices = self.list_devices()
        if device_id not in connected_devices:
            raise ValueError(f"Device ID {device_id} is not connected.")

    def is_path_writable(self, path):
        """Check if the given path is writable."""
        directory = os.path.dirname(path) or "."
        if not os.access(directory, os.W_OK):
            raise PermissionError(f"Path {path} is not writable.")

    def ensure_directory_exists(self, path):
        """Ensure that the directory for the given path exists."""
        directory = os.path.dirname(path) or "."
        if not os.path.exists(directory):
            os.makedirs(directory)
            self.log_message(f"Created directory: {directory}")

    def execute_command(self, device_id, command):
        """Execute an ADB shell command on a specific device.

        Args:
            device_id (str): The ID of the target device.
            command (str): The shell command to execute.

        Returns:
            str: The command output.
        """
        try:
            self.check_adb_installed()
            self.validate_device_id(device_id)
            result = subprocess.run(["adb", "-s", device_id, "shell", command], capture_output=True, text=True, check=True)
            self.log_message(f"Command output: {result.stdout.strip()}")
            return result.stdout.strip()
        except Exception as e:
            self.log_message(f"Failed to execute command: {e}", level=logging.ERROR)
            raise RuntimeError(f"Failed to execute command: {e}")

    def capture_screenshot(self, device_id, save_path="screenshot.png"):
        """Capture a screenshot from a specific device.

        Args:
            device_id (str): The ID of the target device.
            save_path (str): Path to save the screenshot.

        Returns:
            str: Path to the saved screenshot.
        """
        try:
            self.check_adb_installed()
            self.validate_device_id(device_id)
            self.ensure_directory_exists(save_path)  # Ensure directory exists
            self.is_path_writable(save_path)  # Check if path is writable
            with open(save_path, "wb") as f:
                subprocess.run(["adb", "-s", device_id, "exec-out", "screencap", "-p"], stdout=f, check=True)
            self.log_message(f"Screenshot saved to {save_path}")
            return save_path
        except PermissionError as e:
            self.log_message(f"Permission error: {e}", level=logging.ERROR)
            raise
        except Exception as e:
            self.log_message(f"Failed to capture screenshot: {e}", level=logging.ERROR)
            raise RuntimeError(f"Failed to capture screenshot: {e}")

    def tap(self, device_id, x, y):
        """Simulate a tap on the device screen.

        Args:
            device_id (str): The ID of the target device.
            x (int): X-coordinate of the tap.
            y (int): Y-coordinate of the tap.
        """
        try:
            self.check_adb_installed()
            self.validate_device_id(device_id)
            subprocess.run(["adb", "-s", device_id, "shell", f"input tap {x} {y}"], check=True)
            self.log_message(f"Tapped on ({x}, {y}) on device {device_id}")
        except Exception as e:
            self.log_message(f"Failed to tap on ({x}, {y}): {e}", level=logging.ERROR)
            raise RuntimeError(f"Failed to tap on ({x}, {y}): {e}")

    def swipe(self, device_id, x1, y1, x2, y2, duration=300):
        """Simulate a swipe gesture on the device screen.

        Args:
            device_id (str): The ID of the target device.
            x1 (int): Starting X-coordinate.
            y1 (int): Starting Y-coordinate.
            x2 (int): Ending X-coordinate.
            y2 (int): Ending Y-coordinate.
            duration (int): Duration of the swipe in milliseconds (default is 300ms).
        """
        try:
            self.check_adb_installed()
            self.validate_device_id(device_id)
            subprocess.run(["adb", "-s", device_id, "shell", f"input swipe {x1} {y1} {x2} {y2} {duration}"], check=True)
            self.log_message(f"Swiped from ({x1}, {y1}) to ({x2}, {y2}) on device {device_id}")
        except Exception as e:
            self.log_message(f"Failed to swipe: {e}", level=logging.ERROR)
            raise RuntimeError(f"Failed to swipe: {e}")

    def get_screen_resolution(self, device_id):
        """Retrieve the screen resolution of the device.

        Args:
            device_id (str): The ID of the target device.

        Returns:
            tuple: Screen resolution as (width, height).
        """
        try:
            self.check_adb_installed()
            self.validate_device_id(device_id)
            result = subprocess.run(["adb", "-s", device_id, "shell", "wm size"], capture_output=True, text=True, check=True)
            match = re.search(r"Physical size: (\d+)x(\d+)", result.stdout)
            if not match:
                raise ValueError("Failed to retrieve screen resolution.")
            width, height = map(int, match.groups())
            self.log_message(f"Screen resolution of {device_id}: ({width}, {height})")
            return width, height
        except Exception as e:
            self.log_message(f"Failed to get screen resolution: {e}", level=logging.ERROR)
            raise RuntimeError(f"Failed to get screen resolution: {e}")

# Example usage
if __name__ == "__main__":
    adb = ADBModule()

    # List connected devices
    try:
        devices = adb.list_devices()
        print("Connected devices:", devices)
    except RuntimeError as e:
        print(e)

    # Example interactions with a specific device (if any connected devices exist)
    if devices:
        device_id = devices[0]

        # Capture a screenshot
        try:
            screenshot_path = adb.capture_screenshot(device_id, save_path="screenshot.png")
            print(f"Screenshot saved at: {screenshot_path}")
        except RuntimeError as e:
            print(e)

        # Tap on the screen
        try:
            adb.tap(device_id, 500, 500)
        except RuntimeError as e:
            print(e)

        # Swipe on the screen
        try:
            adb.swipe(device_id, 100, 100, 400, 400, duration=500)
        except RuntimeError as e:
            print(e)

        # Get screen resolution
        try:
            resolution = adb.get_screen_resolution(device_id)
            print("Screen resolution:", resolution)
        except RuntimeError as e:
            print(e)
