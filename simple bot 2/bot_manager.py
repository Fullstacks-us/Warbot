# bot_manager.py

import os
import time

# Import all your existing modules
from adb_module import ADBModule
from mapscanner import MapScanner
from navigation_tool import NavigationTool
from digest_screenshots import ScreenshotDigestor
# The screenshot_processor is used inside digest, so typically you don't need
# to import it separately here unless you want direct access.
# from screenshot_processor import ScreenshotProcessor

class BotManager:
    """
    High-level manager that ties together:
      - MapScanner (to scan tiles, capture pop-ups)
      - ScreenshotDigestor (to process/digest resulting screenshots)
      - NavigationTool (to move around in the game)
      - ADBModule (underlying ADB operations)
    """

    def __init__(self,
                 screenshot_dir="screenshots",
                 db_path="map_data.db"):
        # Instantiate the shared ADB module
        self.adb_module = ADBModule()

        # Optional: pass the same ADB instance to each tool
        self.map_scanner = MapScanner(
            db_path=db_path,
            adb=self.adb_module,
            screenshot_dir=screenshot_dir
        )
        self.digestor = ScreenshotDigestor(
            screenshots_dir=screenshot_dir,
            db_path=db_path
        )
        self.nav_tool = NavigationTool(adb=self.adb_module)

        self.screenshot_dir = screenshot_dir
        self.db_path = db_path

    def run_scan_and_digest(self):
        """
        Example workflow:
        1. Use MapScanner to scan a region of the map and capture pop-up screenshots.
        2. After the scan, run the digest to parse the 'center tile' & 'clicked tile' coords.
        """
        print("[MANAGER] Starting map scan...")
        # You can change these coords to match your scanning region
        self.map_scanner.scan_map(
            start_x=90, end_x=1570, step_x=100,
            start_y=90, end_y=800, step_y=100
        )

        print("[MANAGER] Map scan complete. Now digesting the screenshots...")
        self.digestor.digest_all_screenshots()
        print("[MANAGER] Digest complete!")

    def navigate_and_scan(self, kingdom, x, y):
        """
        Example method showing how to:
        1. Use NavigationTool to jump to a specific location (kingdom, x, y)
        2. Then do a quick scan of that area
        """
        device_id = self.map_scanner.device_id
        if not device_id:
            print("[MANAGER] No valid device found. Cannot navigate or scan.")
            return

        print(f"[MANAGER] Navigating to K={kingdom}, X={x}, Y={y}...")
        self.nav_tool.navigate_to_coordinates(
            device_id=device_id,
            kingdom=kingdom,
            x=x,
            y=y
        )
        # Wait a bit for the map to load
        time.sleep(2.0)

        print("[MANAGER] Running a quick map scan around this location...")
        # Just an example: scanning a smaller region near (90, 90)
        self.map_scanner.scan_map(
            start_x=90, end_x=590, step_x=50,
            start_y=90, end_y=390, step_y=50
        )

        print("[MANAGER] Done with navigate_and_scan.")

    def just_digest(self):
        """
        If you only want to digest existing screenshots without scanning.
        """
        self.digestor.digest_all_screenshots()

if __name__ == "__main__":
    manager = BotManager(
        screenshot_dir="screenshots",
        db_path="map_data.db"
    )

    # Example usage #1: Full scan + digest
    manager.run_scan_and_digest()

    # Example usage #2: Navigate somewhere, then scan
    # manager.navigate_and_scan(kingdom=123, x=250, y=400)

    # Example usage #3: Only digest existing screenshots
    # manager.just_digest()
