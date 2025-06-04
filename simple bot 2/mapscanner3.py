import json
import os
import sqlite3
import time
import random
import cv2
import pytesseract
import re
from datetime import datetime
from adb_module import ADBModule
from screenshot_processor import ScreenshotProcessor
from PIL import Image
from fuzzywuzzy import fuzz  # Install with: pip install fuzzywuzzy


class MapScanner:
    def __init__(self, screenshots_dir="screenshots", db_path="map_data.db", step=100, roi_file="rois.json"):
        self.screenshots_dir = screenshots_dir
        self.db_path = db_path
        self.step = step
        self.processor = ScreenshotProcessor()
        self.adb = ADBModule()
        self.roi_file = roi_file
        self.ocr_config = r'--psm 6'  # OCR mode

        if not os.path.exists(self.roi_file):
            print(f"❌ ROI file {self.roi_file} not found. Exiting.")
            exit(1)

        with open(self.roi_file, "r") as f:
            self.rois = json.load(f)

        self._initialize_database()

    def _initialize_database(self):
        """Creates the database if it doesn’t exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS digested_screenshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    adb_x INTEGER,
                    adb_y INTEGER,
                    timestamp TEXT,
                    center_k INTEGER,
                    center_x INTEGER,
                    center_y INTEGER,
                    tile_type TEXT,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def process_range_from_rois(self):
        """Scan tiles based on ROIs."""
        with open(self.roi_file, "r") as f:
            rois = json.load(f).get("tile_scanning", [])

        for roi in rois:
            start_x, start_y, end_x, end_y = map(int, roi)
            for x in range(start_x, end_x, self.step):
                for y in range(start_y, end_y, self.step):
                    self.process_tile(x, y)

    def is_popup_present(self, screenshot_path):
        """Detects if a pop-up is visible before running OCR."""
        possible_popup_rois = [
            (700, 200, 1100, 350),  # Main ROI
            (650, 190, 1150, 370),  # Slightly larger backup ROI
            (725, 220, 1075, 340)   # Slightly smaller backup ROI
        ]

        time.sleep(0.5)  # Small delay to let the pop-up fully load

        for roi in possible_popup_rois:
            extracted_text = self.ocr_from_roi(screenshot_path, roi)
            if len(extracted_text.strip()) > 2:
                print(f"🔍 Pop-up detected using ROI: {roi}")
                return True

        return False

    def process_tile(self, adb_x, adb_y):
        """Processes a single tile: taps, extracts info, and logs results."""
        print(f"🔍 Processing tile at ({adb_x}, {adb_y})")

        self.adb.tap_screen(adb_x, adb_y)
        time.sleep(random.uniform(0.6, 1.0))  

        screenshot_path = os.path.join(self.screenshots_dir, f"popup_{adb_x}_{adb_y}.png")
        success = self.adb.capture_screenshot(screenshot_path)

        if not success or not os.path.exists(screenshot_path):
            print(f"❌ Failed to capture valid screenshot for ({adb_x}, {adb_y})")
            return

        if not self.is_popup_present(screenshot_path):
            print(f"⚠️ No pop-up detected at ({adb_x}, {adb_y}). Skipping OCR.")
            return

        k_val, x_val, y_val = self.extract_tile_coordinates(screenshot_path)
        node_type = self.determine_tile_type(screenshot_path)

        print(f"📍 Tile ({adb_x}, {adb_y}) detected as {node_type} at K:{k_val}, X:{x_val}, Y:{y_val}")

        self.store_in_db(adb_x, adb_y, k_val, x_val, y_val, node_type)

        print(f"⬅️ Pressing ESC to close pop-up for ({adb_x}, {adb_y})")
        self.adb.press_escape()
        time.sleep(random.uniform(0.4, 0.8))

if __name__ == "__main__":
    scanner = MapScanner()
    scanner.process_range_from_rois()
