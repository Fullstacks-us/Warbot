import os
import json
import logging
import logging.handlers  # Explicit import for handlers
import asyncio
import threading
import multiprocessing
from adb_module import ADBModule  # Assuming ADBModule is in the project folder
import matplotlib.pyplot as plt
class BaseModule:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.adb = ADBModule()
        self.logger = logging.getLogger("BaseModule")
        self._setup_logging()

        self.calibration_data = {}
        self.load_config()

    def _setup_logging(self):
        """Set up logging with rotation and verbosity levels."""
        # Fix the import issue and setup logging properly
        log_handler = logging.handlers.RotatingFileHandler(
            "base_module.log", maxBytes=5 * 1024 * 1024, backupCount=3
        )
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        log_handler.setFormatter(formatter)
        self.logger.addHandler(log_handler)
        self.logger.setLevel(logging.INFO)

    def load_config(self):
        """Load configuration from a file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    self.calibration_data = json.load(f)
                    self.logger.info("Configuration loaded successfully.")
            except json.JSONDecodeError as e:
                self.logger.error(f"Error decoding JSON in config file: {e}")
        else:
            self.logger.warning("Configuration file not found. Starting with default settings.")

    def save_config(self):
        """Save calibration data to a configuration file."""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.calibration_data, f, indent=4)
                self.logger.info("Configuration saved successfully.")
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")

    def calibrate_offset(self, retries=3):
        """Calibrate device offsets with retry mechanism."""
        for attempt in range(retries):
            try:
                self.logger.info(f"Attempting calibration (attempt {attempt + 1})...")
                offset = self.adb.get_offset()
                if offset:
                    self.calibration_data["offset"] = offset
                    self.save_config()
                    self.logger.info("Calibration successful.")
                    return
            except Exception as e:
                self.logger.error(f"Calibration attempt {attempt + 1} failed: {e}")
        self.logger.critical("Calibration failed after maximum retries.")

    def validate_grid_point(self, point):
        """Validate a grid point."""
        if not isinstance(point, tuple) or len(point) != 2:
            raise ValueError("Grid point must be a tuple of (x, y).")
        if not all(isinstance(coord, int) and coord >= 0 for coord in point):
            raise ValueError("Grid coordinates must be non-negative integers.")

    def process_grid(self, grid_points):
        """Process grid points using parallelization."""
        def process_point(point):
            self.validate_grid_point(point)
            self.logger.info(f"Processing grid point: {point}")
            # Placeholder for actual processing logic

        with multiprocessing.Pool() as pool:
            pool.map(process_point, grid_points)

    def visualize_grid(self, grid_points, style="default"):
        """Visualize the grid with customizable styles."""
        

        styles = {
            "default": {"color": "blue", "marker": "o"},
            "highlight": {"color": "red", "marker": "x"}
        }

        if style not in styles:
            self.logger.warning(f"Unknown style '{style}'. Falling back to default.")
            style = "default"

        plt.figure(figsize=(8, 8))
        for point in grid_points:
            plt.scatter(point[0], point[1], **styles[style])

        plt.title("Grid Visualization")
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.grid(True)
        plt.show()

# Example unittests for BaseModule
if __name__ == "__main__":
    import unittest

    class TestBaseModule(unittest.TestCase):
        def setUp(self):
            self.base_module = BaseModule()

        def test_validate_grid_point(self):
            self.base_module.validate_grid_point((10, 20))  # Should pass
            with self.assertRaises(ValueError):
                self.base_module.validate_grid_point("invalid")

        def test_calibrate_offset(self):
            self.base_module.calibrate_offset(retries=1)
            self.assertIn("offset", self.base_module.calibration_data)

    unittest.main()
