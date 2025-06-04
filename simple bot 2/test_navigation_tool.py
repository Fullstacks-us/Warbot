import os
import logging

from adb_module import ADBModule
from navigation_tool import NavigationTool
from mapscanner import MapScanner

class PopupCoordinateLogger:
    """
    Simple helper that writes only the pop-up tile coordinates
    to a dedicated logfile (e.g., 'popup_coords.log').
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
                 x=505,
                 y=1017,
                 start_x=90, end_x=700, step_x=100,
                 start_y=90, end_y=800, step_y=100,
                 screenshot_dir="screenshots",
                 db_path="map_data.db",
                 popup_logfile="popup_coords.log"):
        """
        :param kingdom, x, y: where to navigate using the NavigationTool
        :param start_x, end_x, step_x, start_y, end_y, step_y: how MapScanner will loop over tiles
        :param screenshot_dir: directory to store screenshots
        :param db_path: path to the SQLite database
        :param popup_logfile: file where we store ONLY pop-up coordinates
        """
        self.adb = ADBModule()
        self.nav_tool = NavigationTool(adb=self.adb)

        self.map_scanner = MapScanner(
            db_path=db_path,
            adb=self.adb,
            screenshot_dir=screenshot_dir
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

        # We'll attach a custom logger that writes only the pop-up coords
        self.popup_logger = PopupCoordinateLogger(logfile=popup_logfile)

        # Hook into MapScanner's 'store_coordinates' so we can log coordinates ourselves
        self._install_popup_logging_hook()

    def _install_popup_logging_hook(self):
        """
        Replace the map_scanner's 'store_coordinates' method with
        our own wrapper that logs only pop-up coords to a separate file.
        """
        original_store = self.map_scanner.store_coordinates

        def wrapped_store_coordinates(adb_x, adb_y, k_val, x_val, y_val):
            # Call the original store method (which inserts into the 'tiles' table).
            original_store(adb_x, adb_y, k_val, x_val, y_val)

            # Then log these coords to popup_coords.log
            if k_val and x_val and y_val:
                self.popup_logger.log_coordinates(adb_x, adb_y, k_val, x_val, y_val)

        # Overwrite the map_scanner's method with our wrapped version
        self.map_scanner.store_coordinates = wrapped_store_coordinates

    def run(self):
        """
        1. Use NavigationTool to jump to (kingdom, x, y).
        2. Use MapScanner to scan the specified tile range.
        """
        device_id = self.map_scanner.device_id
        if not device_id:
            print("No valid ADB device found. Exiting.")
            return

        # 1) Navigate
        print(f"Navigating to K={self.kingdom}, X={self.tile_x}, Y={self.tile_y}...")
        self.nav_tool.navigate_to_coordinates(
            device_id=device_id,
            kingdom=self.kingdom,
            x=self.tile_x,
            y=self.tile_y
        )

        # Optional: wait for the map to load
        # time.sleep(2)

        # 2) Scan
        print("Starting tile scan...")
        self.map_scanner.scan_map(
            start_x=self.start_x,
            end_x=self.end_x,
            step_x=self.step_x,
            start_y=self.start_y,
            end_y=self.end_y,
            step_y=self.step_y
        )
        print("Tile scan complete. Check popup_coords.log for pop-up coordinates.")

if __name__ == "__main__":
    # Example usage
    runner = NavigatorScanner(
        kingdom=1693,    # The kingdom to navigate
        x=505,           # The X coordinate
        y=1017,          # The Y coordinate
        start_x=90, end_x=200, step_x=100,
        start_y=90, end_y=200, step_y=100,
        screenshot_dir="screenshots",
        db_path="map_data.db",
        popup_logfile="popup_coords.log"
    )
    runner.run()
