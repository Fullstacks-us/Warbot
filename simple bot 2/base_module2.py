import os
import json
import subprocess
from PIL import Image, ImageFilter, ImageOps
import pytesseract
import re
import logging
import cv2
import numpy as np
import asyncio

class BaseModule:
    def __init__(self, device_id=None):
        self.device_id = device_id
        self.offset_x = 0
        self.offset_y = 0
        self.saved_sequences = {}
        self.universal_delay = 200
        self.config = {}

        # Set up logging
        self.logger = logging.getLogger("BaseModule")
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

        # Load default or user-defined configurations
        self.load_config()

    def execute_adb_command(self, command):
        """Execute an ADB command with the specified device ID."""
        try:
            if self.device_id:
                command = ["adb", "-s", self.device_id] + command
            else:
                command = ["adb"] + command

            result = subprocess.check_output(command).decode()
            return result
        except subprocess.CalledProcessError as e:
            self.logger.error(f"ADB command failed: {e}")
            raise

    def calibrate(self):
        """Calibrate the device by getting the screen size."""
        try:
            output = self.execute_adb_command(["shell", "wm", "size"])
            self.logger.info(f"Screen size: {output}")
        except Exception as e:
            self.logger.error(f"Calibration failed: {e}")
            raise

    def capture_screenshot(self, grid_point):
        """Capture a screenshot for a specific grid point."""
        try:
            output = self.execute_adb_command(["exec-out", "screencap", "-p"])
            self.logger.info(f"Captured screenshot for grid point {grid_point}")
            return output
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error processing grid point {grid_point}: {e.output.decode()}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error processing grid point {grid_point}: {e}")
            raise

    def log_message(self, message, level=logging.INFO):
        """Log messages at the specified logging level."""
        self.logger.log(level, message)

    def load_config(self, config_file="config.json"):
        """Load configuration settings from a file."""
        try:
            if os.path.exists(config_file):
                with open(config_file, "r") as f:
                    self.config = json.load(f)
                self.log_message("Configuration loaded successfully.")
            else:
                self.config = {"step": 1, "output_dir": "screenshots"}  # Default settings
                self.log_message("Configuration file not found. Using default settings.", level=logging.WARNING)
        except Exception as e:
            self.log_message(f"Error loading configuration: {e}", level=logging.ERROR)

    def calibrate_offset(self):
        """Calibrate offset using ADB and a center tap."""
        try:
            result = subprocess.run(["adb", "shell", "wm size"], capture_output=True, text=True, check=True)
            match = re.search(r"Physical size: (\d+)x(\d+)", result.stdout)
            if not match:
                raise ValueError("Failed to retrieve screen dimensions.")

            screen_width, screen_height = map(int, match.groups())
            center_x, center_y = screen_width // 2, screen_height // 2

            subprocess.run(["adb", "shell", f"input tap {center_x} {center_y}"], check=True)

            screenshot_path = "screenshot.png"
            subprocess.run(["adb", "exec-out", "screencap", "-p"], stdout=open(screenshot_path, "wb"), check=True)

            image = Image.open(screenshot_path)
            touch_region = image.crop((0, 0, screen_width, screen_height // 10))
            
            # Debugging: Save the cropped region for inspection
            touch_region.save("debug_touch_region.png")

            # Convert to grayscale and apply thresholding
            touch_region = touch_region.convert("L")
            np_image = np.array(touch_region)
            np_image = cv2.adaptiveThreshold(np_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            
            # Debugging: Save the processed image for inspection
            Image.fromarray(np_image).save("debug_processed_touch_region.png")

            touch_text = pytesseract.image_to_string(Image.fromarray(np_image))

            # Debugging: Log the extracted text
            self.log_message(f"Extracted text: {touch_text.strip()}")

            match = re.search(r"\b(\d+),(\d+)\b", touch_text)
            if not match:
                raise ValueError("Failed to extract touch coordinates from screenshot.")

            reported_x, reported_y = map(int, match.groups())
            self.offset_x = reported_x - center_x
            self.offset_y = reported_y - center_y

            self.log_message(f"Calibration successful. Offset: ({self.offset_x}, {self.offset_y})")
            return self.offset_x, self.offset_y

        except Exception as e:
            self.log_message(f"Calibration failed: {e}", level=logging.ERROR)
            raise RuntimeError(f"Calibration failed: {e}")

    async def capture_and_process_point(self, x, y):
        """Capture and process a single grid point asynchronously."""
        try:
            screenshot_path = f"screenshots/grid_{x}_{y}.png"
            subprocess.run(["adb", "exec-out", "screencap", "-p"], stdout=open(screenshot_path, "wb"), check=True)

            image = Image.open(screenshot_path).convert("L")
            np_image = np.array(image)

            # Adaptive thresholding
            np_image = cv2.adaptiveThreshold(np_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            text = pytesseract.image_to_string(Image.fromarray(np_image))

            self.log_message(f"OCR at ({x}, {y}): {text.strip()}")
            return {"x": x, "y": y, "text": text}
        except Exception as e:
            self.log_message(f"Error processing grid point ({x}, {y}): {e}", level=logging.ERROR)

    async def perform_ocr_grid_iteration_async(self, start_x, start_y, end_x, end_y, step=None):
        """Perform OCR on a grid asynchronously."""
        try:
            step = step or self.config.get("step", 1)
            tasks = []
            for x in range(start_x, end_x + 1, step):
                for y in range(start_y, end_y + 1, step):
                    tasks.append(self.capture_and_process_point(x, y))
            return await asyncio.gather(*tasks)
        except Exception as e:
            self.log_message(f"Async OCR Grid Iteration failed: {e}", level=logging.ERROR)
            raise RuntimeError(f"Async OCR Grid Iteration failed: {e}")

    def save_sequence(self, sequence, file_path):
        """Save a sequence to a JSON file."""
        try:
            with open(file_path, "w") as f:
                json.dump(sequence, f)
            self.log_message(f"Sequence saved to {file_path}")
        except Exception as e:
            self.log_message(f"Failed to save sequence: {e}", level=logging.ERROR)
            raise RuntimeError(f"Failed to save sequence: {e}")

    def load_sequences(self, directory):
        """Load sequences from a directory of JSON files."""
        try:
            self.saved_sequences = {}
            os.makedirs(directory, exist_ok=True)
            for filename in os.listdir(directory):
                if filename.endswith(".json"):
                    filepath = os.path.join(directory, filename)
                    with open(filepath, "r") as f:
                        self.saved_sequences[filename] = json.load(f)
            self.log_message(f"Loaded sequences from {directory}")
            return self.saved_sequences
        except Exception as e:
            self.log_message(f"Failed to load sequences: {e}", level=logging.ERROR)
            raise RuntimeError(f"Failed to load sequences: {e}")

    def list_connected_devices(self):
        """List all connected ADB devices."""
        try:
            result = subprocess.run(["adb", "devices"], capture_output=True, text=True, check=True)
            devices = [line.split()[0] for line in result.stdout.splitlines() if "\tdevice" in line]
            self.log_message(f"Connected devices: {devices}")
            return devices
        except Exception as e:
            self.log_message(f"Failed to list devices: {e}", level=logging.ERROR)
            raise RuntimeError(f"Failed to list devices: {e}")

    def ensure_directory(self, directory):
        """Ensure a directory exists."""
        os.makedirs(directory, exist_ok=True)

    def visualize_grid_results(self, results):
        """Visualize OCR results on a grid."""
        try:
            import matplotlib.pyplot as plt

            plt.figure(figsize=(10, 10))
            for result in results:
                x, y, text = result["x"], result["y"], result["text"]
                plt.scatter(x, y, label=text[:10])  # Show part of the text
            plt.legend()
            plt.grid(True)
            plt.show()
        except ImportError:
            self.log_message("matplotlib is not installed. Visualization skipped.", level=logging.WARNING)
        except Exception as e:
            self.log_message(f"Failed to visualize results: {e}", level=logging.ERROR)

# Example Usage
if __name__ == "__main__":
    # Replace 'your_device_id' with the actual device ID
    base_module = BaseModule(device_id='your_device_id')

    # Calibrate offset
    try:
        offset = base_module.calibrate_offset()
        print(f"Calibrated Offset: {offset}")
    except RuntimeError as e:
        print(e)

    # Perform asynchronous OCR grid iteration
    try:
        results = asyncio.run(base_module.perform_ocr_grid_iteration_async(0, 0, 5, 5))
        print("OCR Results:")
        for result in results:
            print(result)
    except RuntimeError as e:
        print(e)
