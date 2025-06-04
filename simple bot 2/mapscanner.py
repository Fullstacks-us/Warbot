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

    def is_popup_present(self, screenshot_path):
        """Detects if a pop-up is visible before running OCR."""
        possible_popup_rois = [
            (700, 200, 1100, 350),
            (650, 190, 1150, 370),
            (725, 220, 1075, 340)
        ]

        time.sleep(0.5)

        for roi in possible_popup_rois:
            extracted_text = self.ocr_from_roi(screenshot_path, roi)
            if len(extracted_text.strip()) > 2:
                print(f"🔍 Pop-up detected using ROI: {roi}")
                return True

        return False

    def determine_tile_type(self, screenshot_path):
        """Determines the tile type dynamically using fuzzy matching."""
        priority_order = {
            "castle": ["troops killed", "might"],
            "darknest": ["dark nest"],
            "monster": ["monster", "creature"],
            "resource": ["rich vein", "field", "ruins", "rocks", "woods"],
            "vacant": ["forest", "magma path", "glacier", "mountain", "sea", "shore", "volcano", "lava hill"]
        }

        for node_type, keywords in priority_order.items():
            for roi in self.rois["node_types"].get(node_type, []):
                extracted_text = self.ocr_from_roi(screenshot_path, roi)
                for keyword in keywords:
                    similarity = fuzz.ratio(keyword, extracted_text)
                    if similarity > 75:
                        print(f"🔍 Matched {keyword} → {node_type} (Similarity: {similarity}%)")
                        return node_type

        print(f"⚠️ No match found. Tile classified as 'unknown'.")
        return "unknown"

    def extract_tile_coordinates(self, screenshot_path):
        """Extracts (K, X, Y) from OCR."""
        for roi in self.rois["ocr_regions"]:
            extracted_text = self.ocr_from_roi(screenshot_path, roi)
            match = self.parse_coordinates(extracted_text)
            if match:
                return match

        return None, None, None

    def ocr_from_roi(self, image_path, roi):
        """Extracts text from a specified ROI using OCR."""
        x1, y1, x2, y2 = sorted(map(int, roi))

        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f"❌ Could not read image: {image_path}")
            return ""

        height, width = img.shape
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(width, x2), min(height, y2)

        if x1 >= x2 or y1 >= y2:
            print(f"⚠️ Invalid ROI {roi}. Skipping OCR.")
            return ""

        cropped = img[y1:y2, x1:x2]

        # Enhance image for OCR
        _, cropped = cv2.threshold(cropped, 128, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        text = pytesseract.image_to_string(cropped, config=self.ocr_config).strip()

        if text:
            print(f"✅ OCR detected text: '{text}'")
        else:
            print(f"⚠️ OCR found NO TEXT for ROI: {roi}")

        return text if text else "NO_TEXT_DETECTED"

    def parse_coordinates(self, text):
        """Parses coordinates (K, X, Y) from OCR output."""
        match = re.search(r"K\s*[:=]?\s*(\d+)\s*X\s*[:=]?\s*(\d+)\s*Y\s*[:=]?\s*(\d+)", text, re.IGNORECASE)
        return tuple(map(int, match.groups())) if match else (None, None, None)

    def store_in_db(self, adb_x, adb_y, k, x, y, node_type):
        """Stores results in SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO digested_screenshots 
                (adb_x, adb_y, timestamp, center_k, center_x, center_y, tile_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (adb_x, adb_y, datetime.now().strftime("%Y%m%d_%H%M%S"), k, x, y, node_type))

if __name__ == "__main__":
    scanner = MapScanner()
    scanner.process_range_from_rois()
