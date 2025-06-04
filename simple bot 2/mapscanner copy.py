import logging
import time
import json
from navigation_tool import NavigationTool
from adb_module import ADBModule
from ocr_module import OCRModule
from datetime import datetime

class TileScanner:
    def __init__(self, roi_file="rois.json"):
        self.adb = ADBModule()
        self.nav_tool = NavigationTool(adb=self.adb)
        self.ocr = OCRModule()
        self.logger = logging.getLogger("TileScanner")
        self.tiles_scanned = []
        self.roi_file = roi_file
        self._setup_logging()
        self.load_rois()

        # Tile type keyword mapping for OCR
        self.tile_mapping = {
            "castle": ["troops killed", "might"],
            "darknest": ["darknest"],
            "monster": ["monster", "creature"],
            "resource": ["rich vein", "field", "ruins", "rocks", "woods"],
            "vacant": ["forest", "magma path", "glacier", "mountain", "sea", "shore", "volcano", "lava hill"]
        }

    def identify_tile_type(self, extracted_text):
        """Determine tile type based on OCR-extracted text."""
        for tile, keywords in self.tile_mapping.items():
            if any(keyword in extracted_text for keyword in keywords):
                return tile
        return "unknown"



    def _setup_logging(self):
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def load_rois(self):
        """Load predefined ROI positions from JSON file."""
        try:
            with open(self.roi_file, "r") as f:
                self.rois = json.load(f)
            self.logger.info(f"Loaded ROI data: {self.rois}")
        except Exception as e:
            self.logger.error(f"Failed to load ROI data: {e}")
            self.rois = {"tile_scanning": []}  # Default to an empty list

    def scan_tile_at_roi(self, kingdom, x, y, roi_position):
        """Tap on a tile in the ROI, capture a screenshot, and determine tile type."""
        x1, y1, x2, y2 = roi_position  # Extract rectangle coordinates
        tap_x = (x1 + x2) // 2  # Center X
        tap_y = (y1 + y2) // 2  # Center Y

        self.logger.info(f"Scanning tile at {kingdom}:{x},{y} using ROI ({tap_x}, {tap_y})")

        # Tap at the center of the ROI
        self.adb.tap_screen(tap_x, tap_y)
        time.sleep(2)  # Wait for any potential pop-ups

        # Capture a timestamped screenshot for debugging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"screenshots/tile_{kingdom}_{x}_{y}_{tap_x}_{tap_y}_{timestamp}.png"
        if not self.adb.capture_screenshot(screenshot_path):
            self.logger.error("Failed to capture screenshot.")
            return None

        # Extract text from screenshot
        extracted_text = self.ocr.extract_text(screenshot_path).lower()
        tile_type = self.identify_tile_type(extracted_text)

        # Log and save tile type
        tile_data = {"kingdom": kingdom, "x": x, "y": y, "tile_type": tile_type, "tap_x": tap_x, "tap_y": tap_y}
        self.tiles_scanned.append(tile_data)
        self.logger.info(f"Tile identified as: {tile_type}")

        # If tile is unknown, skip further scanning for this tile
        if tile_type == "unknown":
            self.logger.info(f"Skipping unknown tile at {kingdom}:{x},{y}.")
            return None

        # Close pop-up using ESC key
        self.adb.press_escape()
        time.sleep(1)

        # Expand outward and scan surrounding tiles
        self.scan_surrounding_tiles(kingdom, x, y, roi_position)

        return tile_type

    def scan_surrounding_tiles(self, kingdom, x, y, roi_position):
        """Iterate outward from the center tile and scan surrounding tiles."""
        x1, y1, x2, y2 = roi_position  # ROI boundary
        step_size = 50  # Distance between tiles
        max_steps = 3  # Number of tiles to scan outward

        self.logger.info(f"Scanning surrounding tiles at {kingdom}:{x},{y}...")

        # Generate points in a spiral/grid pattern
        for dx in range(-max_steps, max_steps + 1):
            for dy in range(-max_steps, max_steps + 1):
                if dx == 0 and dy == 0:
                    continue  # Skip the center tile (already scanned)

                tap_x = (x1 + x2) // 2 + (dx * step_size)
                tap_y = (y1 + y2) // 2 + (dy * step_size)

                # Ensure tap_x and tap_y are within ROI bounds
                if x1 <= tap_x <= x2 and y1 <= tap_y <= y2:
                    self.logger.info(f"Scanning nearby tile at ({tap_x}, {tap_y})")
                    self.adb.tap_screen(tap_x, tap_y)
                    time.sleep(2)

                    # Capture and analyze new tile
                    screenshot_path = f"screenshots/tile_{kingdom}_{x}_{y}_{tap_x}_{tap_y}.png"
                    if self.adb.capture_screenshot(screenshot_path):
                        extracted_text = self.ocr.extract_text(screenshot_path).lower()
                        tile_type = self.identify_tile_type(extracted_text)
                        self.logger.info(f"Nearby tile identified as: {tile_type}")

                        # Close pop-up before continuing
                        self.adb.press_escape()
                        time.sleep(1)

    def scan_location(self, kingdom, x, y):
        """Navigate to a coordinate and scan all visible tiles using the new expansion method."""
        self.logger.info(f"Navigating to {kingdom}:{x},{y} and scanning tiles.")

        # Move to the specified location
        self.nav_tool.navigate_to_coordinates(kingdom, x, y)
        time.sleep(3)  # Allow UI to load

        # Scan center tile first
        for roi_position in self.rois.get("tile_scanning", []):
            self.scan_tile_at_roi(kingdom, x, y, roi_position)

    def scan_entire_grid(self, kingdom, x_start, x_end, y_start, y_end, move_step=100):
        """Moves in steps across the map, scanning all visible tiles before moving again."""
        self.logger.info(f"Starting full grid scan from ({x_start},{y_start}) to ({x_end},{y_end})")

        for x in range(x_start, x_end + 1, move_step):
            for y in range(y_start, y_end + 1, move_step):
                self.scan_location(kingdom, x, y)
                time.sleep(1)

        with open("tile_scan_results.json", "w") as f:
            json.dump(self.tiles_scanned, f, indent=4)

        self.logger.info("Full grid scan complete.")

if __name__ == "__main__":
    scanner = TileScanner()
    scanner.scan_entire_grid(kingdom=914, x_start=7, x_end=511, y_start=7, y_end=1023, move_step=7)
