# navigation_tool.py

import logging
from adb_module import ADBModule
import time

class NavigationTool:
    def __init__(self, adb=None):
        self.adb = adb or ADBModule()
        self.logger = logging.getLogger("NavigationTool")
        self._setup_logging()

    def _setup_logging(self):
        """Set up logging for NavigationTool."""
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def validate_coordinates(self, kingdom, x, y):
        """Validate coordinates for navigation."""
        if not isinstance(kingdom, (int, type(None))) or not isinstance(x, int) or not isinstance(y, int):
            raise ValueError("Coordinates must be integers (kingdom, x, y).")
        if x < 0 or x > 511 or y < 0 or y > 1023:
            raise ValueError("X and Y coordinates must be between 0 and 1023.")
        self.logger.info(f"Validated coordinates: Kingdom={kingdom}, X={x}, Y={y}")
        return True

    def navigate_to_coordinates(self, kingdom, x, y, last_kingdom=None, last_x=None, last_y=None, retries=3):
        """
        Navigate to the specified coordinates in the game.

        Args:
            kingdom (int): The kingdom number.
            x (int): X coordinate.
            y (int): Y coordinate.
            last_kingdom (int): The last kingdom value (used to decide if an update is needed).
            last_x (int): The last X coordinate value.
            last_y (int): The last Y coordinate value.
            retries (int): Number of retries for navigation.
        """
        self.validate_coordinates(kingdom, x, y)

        # Tap positions for fields and "Go" button
        field_tap_positions = {
            "kingdom": (685, 335),  # Kingdom input field
            "x": (821, 335),        # X coordinate input field
            "y": (969, 335)         # Y coordinate input field
        }
        go_button_position = (765, 467)  # "Go" button

        for attempt in range(retries):
            try:
                self.logger.info(f"Navigating to coordinates: Kingdom={kingdom}, X={x}, Y={y} (Attempt {attempt + 1})")

                # Tap navigation menu button
                self.adb.tap_screen(843, 118)

                # Change kingdom only if it's different from the last kingdom
                if last_kingdom != kingdom:
                    self.logger.info(f"Updating Kingdom to {kingdom}")
                    self._tap_and_enter(field_tap_positions["kingdom"], kingdom)

                # Change X coordinate only if it's different from the last X coordinate
                if last_x != x:
                    self.logger.info(f"Updating X coordinate to {x}")
                    self._tap_and_enter(field_tap_positions["x"], x)

                # Change Y coordinate only if it's different from the last Y coordinate
                if last_y != y:
                    self.logger.info(f"Updating Y coordinate to {y}")
                    self._tap_and_enter(field_tap_positions["y"], y)

                # Tap the "Go" button
                self.logger.info(f"Tapping 'Go' button")
                self.adb.tap_screen(*go_button_position)
                self.logger.info(f"Triggered navigation to specified coordinates.")
                return  # Exit after successful navigation

            except Exception as e:
                self.logger.error(f"Navigation attempt {attempt + 1} failed: {e}")

        self.logger.critical(f"Navigation failed after maximum retries.")

    def _tap_and_enter(self, tap_position, value):
        """Tap on a field and enter a value."""
        keypad_positions = {
            "0": (1098, 619), "1": (1065, 379), "2": (1195, 367),
            "3": (1290, 367), "4": (1065, 430), "5": (1195, 430),
            "6": (1290, 430), "7": (1065, 530), "8": (1195, 530),
            "9": (1290, 530), "check": (1275, 630)  # Checkmark button
        }

        x, y = tap_position
        self.adb.tap_screen(x, y)
        self.logger.info(f"Tapped on input field at position: {tap_position}")

        # Enter value digit by digit
        for digit in str(value):
            if digit in keypad_positions:
                key_x, key_y = keypad_positions[digit]
                self.adb.tap_screen(key_x, key_y)
                self.logger.info(f"Tapped key '{digit}' at position: ({key_x}, {key_y})")
            else:
                raise ValueError(f"Invalid digit '{digit}' for keypad entry.")

        # Tap checkmark to confirm
        check_x, check_y = keypad_positions["check"]
        self.adb.tap_screen(check_x, check_y)
        self.logger.info(f"Tapped checkmark at position: ({check_x}, {check_y})")
