import os
import re
import sqlite3
from datetime import datetime
from screenshot_processor import ScreenshotProcessor

class ScreenshotDigestor:
    """
    Iterates through all screenshots in the `screenshots` folder, parses the
    filename for adb_x/adb_y, then extracts two sets of coordinates using
    ScreenshotProcessor:
      1) 'view center' (ROI at (786,100,1019,137))
      2) 'clicked tile' from up to four possible popup ROIs.
    """

    FILENAME_PATTERN = re.compile(r"^tile_(\d+)_(\d+)_(\d{8}_\d{6})\.png$")

    def __init__(self, screenshots_dir="screenshots", db_path="map_data.db"):
        self.screenshots_dir = screenshots_dir
        self.db_path = db_path
        self.processor = ScreenshotProcessor()
        self._initialize_database()

    def _initialize_database(self):
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
                    clicked_k INTEGER,
                    clicked_x INTEGER,
                    clicked_y INTEGER,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def digest_all_screenshots(self):
        file_list = sorted(os.listdir(self.screenshots_dir))
        for filename in file_list:
            match = self.FILENAME_PATTERN.match(filename)
            if not match:
                continue

            adb_x_str, adb_y_str, date_str = match.groups()
            adb_x, adb_y = int(adb_x_str), int(adb_y_str)
            screenshot_path = os.path.join(self.screenshots_dir, filename)

            # Process the screenshot with multiple ROIs
            center_coords, clicked_coords = self.processor.process_screenshot(
                screenshot_path=screenshot_path,
                roi_center=(786, 100, 1019, 137),
                roi_popup_castle_darknest=(682, 698, 911, 731),
                roi_popup_monster=(340, 715, 569, 746),
                roi_popup_rss_tile=(690, 631, 916, 665),
                roi_popup_vacant_tile=(690, 458, 904, 491)
            )

            center_k, center_x, center_y = center_coords if center_coords else (None, None, None)
            clicked_k, clicked_x, clicked_y = clicked_coords if clicked_coords else (None, None, None)

            self.store_in_db(
                adb_x, adb_y, date_str,
                center_k, center_x, center_y,
                clicked_k, clicked_x, clicked_y
            )

            print(f"File: {filename}")
            print(f"  ADB coords: ({adb_x},{adb_y}) Timestamp: {date_str}")
            print(f"  Center Tile: {center_coords}")
            print(f"  Clicked Tile: {clicked_coords}")
            print("-" * 40)

    def store_in_db(self,
                    adb_x, adb_y, date_str,
                    center_k, center_x, center_y,
                    clicked_k, clicked_x, clicked_y):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO digested_screenshots 
                (adb_x, adb_y, timestamp,
                 center_k, center_x, center_y,
                 clicked_k, clicked_x, clicked_y)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                adb_x, adb_y, date_str,
                center_k, center_x, center_y,
                clicked_k, clicked_x, clicked_y
            ))

def main():
    digestor = ScreenshotDigestor(
        screenshots_dir="screenshots",
        db_path="map_data.db"
    )
    digestor.digest_all_screenshots()

if __name__ == "__main__":
    main()
