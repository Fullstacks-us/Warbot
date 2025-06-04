import json
import time
import threading
from adb_module import ADBModule
from navigation_tool import NavigationTool
from ocr_module import OCRModule


class TileScanner:
    def __init__(self, roi_file="rois.json"):
        self.adb = ADBModule()
        self.nav_tool = NavigationTool(adb=self.adb)
        self.ocr = OCRModule()
        self.tiles_scanned = []
        self.roi_file = roi_file
        self.scanning = False
        self.load_rois()

        self.tile_mapping = {
            "castle": ["troops killed", "might"],
            "darknest": ["dark nest"],
            "monster": ["monster", "creature"],
            "resource": ["rich vein", "field", "ruins", "rocks", "woods"],
            "vacant": ["forest", "magma path", "glacier", "mountain", "sea", "shore", "volcano", "lava hill"]
        }

    def load_rois(self):
        """Loads ROI data from JSON."""
        try:
            with open(self.roi_file, "r") as f:
                self.rois = json.load(f)
        except Exception as e:
            print(f"Failed to load ROI data: {e}")
            self.rois = {"tile_scanning": []}  # Default fallback

    def scan_tile_at_roi(self, kingdom, x, y, roi_position):
        """Scans a single tile at the given ROI position."""
        x1, y1, x2, y2 = roi_position
        tap_x = (x1 + x2) // 2
        tap_y = (y1 + y2) // 2

        print(f"Scanning tile at {kingdom}:{x},{y} using ROI ({tap_x}, {tap_y})")
        self.adb.tap_screen(tap_x, tap_y)
        time.sleep(2)  # Wait for pop-up

        # 🔧 FIX: Generate unique screenshot filename
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"screenshots/tile_{kingdom}_{x}_{y}_{tap_x}_{tap_y}_{timestamp}.png"

        if not self.adb.capture_screenshot(screenshot_path):
            print("Failed to capture screenshot.")
            return None

        extracted_text = self.ocr.extract_text(screenshot_path).lower()
        tile_type = self.identify_tile_type(extracted_text)

        self.tiles_scanned.append({"kingdom": kingdom, "x": x, "y": y, "tile_type": tile_type, "screenshot": screenshot_path})
        print(f"Tile identified as: {tile_type}")

        self.adb.press_escape()
        time.sleep(1)
        return tile_type


    def identify_tile_type(self, extracted_text):
        """Identifies the tile type based on OCR text."""
        for tile, keywords in self.tile_mapping.items():
            if any(keyword in extracted_text for keyword in keywords):
                return tile
        return "unknown"

    def scan_location(self, kingdom, x, y, stop_flag=False):
        """Scan a specific tile while checking if stop is requested."""
        
        if stop_flag:  # ✅ Stop immediately if requested
            return False  # Signal that scan was interrupted

        print(f"Scanning tile at {kingdom}:{x},{y}...")  # Debugging log
        # Add OCR / Screenshot processing here...

        if stop_flag:  # ✅ Check stop flag again before heavy processing
            return False  

        return True  # ✅ Scan completed successfully



    def scan_area(self, kingdom, x_start, x_end, y_start, y_end, step=100):
        """Scans multiple locations using ROIs."""
        print(f"Starting area scan from ({x_start},{y_start}) to ({x_end},{y_end})")
        self.scanning = True

        for x in range(x_start, x_end + 1, step):
            for y in range(y_start, y_end + 1, step):
                if not self.scanning:
                    return
                self.scan_location(kingdom, x, y)
                time.sleep(1)

        with open("tile_scan_results.json", "w") as f:
            json.dump(self.tiles_scanned, f, indent=4)
        print("Area scan complete.")

    def stop_scan(self):
        """Stops scanning."""
        self.scanning = False
