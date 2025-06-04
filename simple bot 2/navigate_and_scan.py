# navigate_and_scan.py

import os
import logging
from adb_module import ADBModule
from navigation_tool import NavigationTool
from mapscanner import MapScanner
import time

class PopupCoordinateLogger:
    """
    Helper class to log only the pop-up tile coordinates to a dedicated logfile.
    """
    def __init__(self, logfile="popup_coords.log"):
        self.logfile = logfile

    def log_coordinates(self, adb_x, adb_y, k_val, x_val, y_val):
        """
        Write the pop-up's K, X, Y (and the tile's ADB coords) to a file.
        Only does so if K, X, Y are not None.
        """
        if k_val is not None and x_val is not None and y_val is not None:
            log_line = f"ADB({adb_x},{adb_y}) => K={k_val}, X={x_val}, Y={y_val}\n"
            with open(self.logfile, "a", encoding="utf-8") as f:
                f.write(log_line)

class NavigatorScanner:
    """
    1. Navigates the map to (kingdom=1693, x=507, y=1017).
    2. Scans a specified set of tiles with MapScanner.
    3. Logs only the pop-up coordinates to a separate log file.
    """

    def __init__(self,
                 kingdom=1693,
                 x=507,
                 y=1017,
                 start_x=90, end_x=1570, step_x=100,
                 start_y=90, end_y=800, step_y=100,
                 screenshot_dir="screenshots",
                 db_path="map_data.db",
                 popup_logfile="popup_coords.log"):
        """
        :param kingdom, x, y: Coordinates to navigate using the NavigationTool
        :param start_x, end_x, step_x, start_y, end_y, step_y: Tile scanning range
        :param screenshot_dir: Directory to store screenshots
        :param db_path: Path to the SQLite database
        :param popup_logfile: File where pop-up coordinates are logged
        """
        self.adb = ADBModule()
        self.nav_tool = NavigationTool(adb=self.adb)
        self.map_scanner = MapScanner(
            screenshots_dir=screenshot_dir,
            db_path=db_path
        )
        self.kingdom = kingdom
        self.tile_x = x
        self.tile_y = y

        self.start_x = start_x
        self.end_x = end_x
        self.step_x = step_x
        self.start_y = start_y
        self.end_y = end_y
        self.step_y = step_y

        # Initialize the popup coordinate logger
        self.popup_logger = PopupCoordinateLogger(logfile=popup_logfile)

        # Hook into MapScanner's 'store_coordinates' method to log pop-up coordinates
        self._install_popup_logging_hook()

    def _install_popup_logging_hook(self):
        """
        Replace the map_scanner's 'store_coordinates' method with
        our own wrapper that logs only pop-up coordinates to a separate file.
        """
        original_store = self.map_scanner.store_coordinates

        def wrapped_store_coordinates(adb_x, adb_y, k_val, x_val, y_val):
            # Call the original store method (which inserts into the 'digested_screenshots' table).
            original_store(adb_x, adb_y, k_val, x_val, y_val)

            # Then log these coords to popup_coords.log
            if k_val is not None and x_val is not None and y_val is not None:
                self.popup_logger.log_coordinates(adb_x, adb_y, k_val, x_val, y_val)

        # Overwrite the map_scanner's method with our wrapped version
        self.map_scanner.store_coordinates = wrapped_store_coordinates

    def run(self):
        """
        1. Use NavigationTool to jump to (kingdom, x, y).
        2. Use MapScanner to scan the specified tile range.
        """
        device_id = self.adb.device_id
        if not device_id:
            print("No valid ADB device found. Exiting.")
            return

        # 1) Navigate
        print(f"Navigating to K={self.kingdom}, X={self.tile_x}, Y={self.tile_y}...")
        self.nav_tool.navigate_to_coordinates(
            kingdom=self.kingdom,
            x=self.tile_x,
            y=self.tile_y
        )

        # Wait a bit for the map to load
        time.sleep(2.0)

        # 2) Scan
        print("Starting tile scan...")
        self.map_scanner.digest_all_screenshots()
        print("Tile scan complete. Check popup_coords.log for pop-up coordinates.")

if __name__ == "__main__":
    # Example usage
    runner = NavigatorScanner(
        kingdom=1693,    # The kingdom to navigate
        x=507,           # The X coordinate
        y=1017,          # The Y coordinate
        start_x=90, end_x=1570, step_x=100,
        start_y=90, end_y=800, step_y=100,
        screenshot_dir="screenshots",
        db_path="map_data.db",
        popup_logfile="popup_coords.log"
    )
    runner.run()
