import os
import sqlite3
import time
import json
import re
import logging
from logging.handlers import RotatingFileHandler
from PIL import Image
from rapidfuzz import fuzz
from spellchecker import SpellChecker
from adb_module import ADBModule
from ocr_module import OCRModule
import sys

class MapScanner:
    def __init__(self, db_path="map_data.db", adb=None, ocr=None, device_id=None, log_file="map_scanner.log"):
        self.db_path = db_path
        self.adb = adb or ADBModule()
        self.ocr = ocr or OCRModule()
        self.device_id = device_id
        self.log_file = log_file
        self.processed_tiles = set()
        self.spell = SpellChecker()
        self._setup_logging()
        self._initialize_database()

        # Coordinates of the “Close” buttons
        self.close_btn_monster = (1545, 55)      # For monster tiles
        self.close_btn_non_monster = (1075, 161) # For everything else

    def _setup_logging(self):
        """Set up console & file logging."""
        self.logger = logging.getLogger("MapScanner")
        self.logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        # Configure stdout/stderr for UTF-8
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        file_handler = RotatingFileHandler(
            self.log_file, 
            maxBytes=5 * 1024 * 1024, 
            backupCount=5, 
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def _initialize_database(self):
        """
        Create the 'tiles' table if it doesn't exist.
        'node_type' and 'details' will store info about the tile type and OCR text.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    adb_x INTEGER,
                    adb_y INTEGER,
                    x INTEGER,
                    y INTEGER,
                    node_type TEXT,
                    details TEXT,
                    kingdom_x INTEGER DEFAULT NULL,
                    kingdom_y INTEGER DEFAULT NULL,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.logger.info("✅ Database initialized successfully.")

    def clean_ocr_text(self, text):
        """
        Cleans up the OCR output by removing unwanted characters or extra whitespace.
        Adjust the regex for your specific OCR output if needed.
        """
        if not text:
            return ""
        text = text.strip()
        # Example: keep letters, digits, underscores, spaces, and colons
        text = re.sub(r"[^\w\s:]", "", text)
        return text

    def take_screenshot(self, filename):
        """Capture a screenshot and save to 'filename'."""
        self.logger.info(f"📸 Capturing screenshot: {filename}")
        self.adb.capture_screenshot(self.device_id, filename)

    def scan_map(self, tile_positions):
        """
        Iterates through each tile position, processes each tile.
        """
        for adb_x, adb_y in tile_positions:
            self.process_tile(adb_x, adb_y)

    def process_tile(self, adb_x, adb_y):
        """
        1. Tap the tile
        2. Capture the pop-up info (screenshot + OCR)
        3. Determine tile type (monster or resource/other)
        4. Tap the correct close button
        5. Save details to the database
        """
        self.logger.info(f"Processing tile at ADB coords: ({adb_x}, {adb_y})")

        # 1. Tap the tile
        self.adb.tap_screen(self.device_id, adb_x, adb_y)
        time.sleep(1)  # short delay to let UI load

        # 2. Take a screenshot of the pop-up (unique name per tile + timestamp)
        timestamp = int(time.time())
        screenshot_path = f"screenshots/tile_{adb_x}_{adb_y}_{timestamp}.png"
        self.take_screenshot(screenshot_path)

        # 3. OCR to check if it's a monster or not
        ocr_text = self.ocr.extract_text(screenshot_path)
        cleaned_text = self.clean_ocr_text(ocr_text)
        cleaned_lower = cleaned_text.lower()
        self.logger.debug(f"OCR text from tile: {cleaned_text}")

        # Default tile type
        tile_type = "other"

        # 4. Decide if it's a monster
        if "monster" in cleaned_lower or "monster hunter" in cleaned_lower or "dmg" in cleaned_lower:
            tile_type = "monster"
            self.logger.info("Detected monster tile. Tapping monster close button.")
            self.adb.tap_screen(self.device_id, *self.close_btn_monster)
        else:
            tile_type = "resource"
            self.logger.info("Detected resource/other tile. Tapping normal close button.")
            self.adb.tap_screen(self.device_id, *self.close_btn_non_monster)

        time.sleep(1)  # optional delay after closing

        # 5. Save tile details to the database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO tiles (adb_x, adb_y, node_type, details)
                VALUES (?, ?, ?, ?)
            """, (adb_x, adb_y, tile_type, cleaned_text))
            conn.commit()
            self.logger.info(f"Tile info saved to DB: (adb_x={adb_x}, adb_y={adb_y}, type={tile_type})")

if __name__ == "__main__":
    # Create an instance with your desired device ID
    scanner = MapScanner(device_id="emulator-5554")

    # Example tile positions
    tile_positions = [
        (65, 184),
        (275, 183),
        (487, 183),
        (685, 183),
        (904, 183),
        (1117, 183),
        (1324, 183),
        (1545, 183),
        
        (154, 228),
        (354, 228),
        (554, 228),
        (754, 228),
        (954, 228),
        (1154, 228),
        (1354, 228),
       
        (69, 283),
        (275, 283),
        (487, 283),
        (685, 283),
        (904, 283),
        (1117, 283),
        (1324, 283),
        (1545, 283),

        (128, 331),
        (348, 331),
        (578, 331),
        (808, 331),
        (1028, 331),
        (1248, 331),
        (1470, 331)
    ]

    scanner.scan_map(tile_positions)
