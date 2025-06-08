import os
import sqlite3
import re
import json
from typing import Tuple, Dict, Optional

from adb_module import ADBModule
from ocr_module import OCRModule
try:
    from sprites_game.mcp_client import MCPClient
except ModuleNotFoundError:  # allow tests run from this folder
    import sys
    import os as _os
    sys.path.append(_os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..")))
    from sprites_game.mcp_client import MCPClient

class NodeMapper:
    """Minimal node mapper used for tests."""
    def __init__(
        self,
        db_path: str = "grid_data.db",
        adb: Optional[ADBModule] = None,
        ocr: Optional[OCRModule] = None,
        device_id: Optional[str] = None,
        mcp_client: Optional[MCPClient] = None,
    ):
        self.db_path = db_path
        self.adb = adb or ADBModule()
        self.ocr = ocr or OCRModule()
        self.device_id = device_id
        self.mcp = mcp_client or MCPClient()
        self.screenshot_dir = "screenshots"
        os.makedirs(self.screenshot_dir, exist_ok=True)
        os.makedirs("raw_text", exist_ok=True)
        self._initialize_db()

    def _initialize_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS grid_data (
                    adb_x INTEGER,
                    adb_y INTEGER,
                    x INTEGER,
                    y INTEGER,
                    node_type TEXT,
                    details TEXT,
                    kingdom TEXT,
                    kingdom_x INTEGER,
                    kingdom_y INTEGER
                )
                """
            )
            conn.commit()

    def clean_ocr_text(self, text: str) -> str:
        if not text:
            return ""
        text = text.replace("|", " ")
        text = re.sub(r"[^0-9A-Za-z,:.!\s]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def classify_node(self, cleaned_text: str) -> Tuple[str, Dict[str, str], Optional[str]]:
        text = cleaned_text.lower()
        details: Dict[str, str] = {}
        kingdom = None

        text_normalized = text.replace("1", "l")
        if "darknest" in text_normalized:
            node_type = "Darknest"
        elif "grassland" in text_normalized and "kingdom" in text_normalized:
            node_type = "Grassland"
        elif "grassland" in text_normalized:
            node_type = "Vacant"
        elif any(k in text_normalized for k in ["guild", "troops killed", "view profile", "might", "rally attack", "scout"]):
            node_type = "Castle"
        elif any(k in text_normalized for k in ["monster", "dmg"]):
            node_type = "Monster"
        elif any(k in text_normalized for k in ["rich vein", "field", "woods", "rocks", "ore", "wood", "stone", "food", "gold"]):
            node_type = "Rss Tile"
        elif any(k in text_normalized for k in [
            "transfer", "vacant", "forest", "magma path", "glacier",
            "mountain", "sea", "shore", "volcano", "lava hill"
        ]):
            node_type = "Vacant"
        else:
            node_type = "Unknown"

        m = re.search(r"kingdom\s*:?\s*(\w+)", cleaned_text, re.IGNORECASE)
        if m:
            kingdom = m.group(1)

        m = re.search(r"guild\s*:?\s*(\w+)", cleaned_text, re.IGNORECASE)
        if m:
            details["guild"] = m.group(1)

        m = re.search(r"might\s*:?\s*([\d,]+)", cleaned_text, re.IGNORECASE)
        if m:
            details["might"] = m.group(1)

        m = re.search(r"troops killed\s*:?\s*([\d,]+)", cleaned_text, re.IGNORECASE)
        if m:
            details["troops_killed"] = m.group(1)

        return node_type, details, kingdom

    def process_node(self, adb_x: int, adb_y: int):
        screenshot_path = os.path.join(self.screenshot_dir, f"node_{adb_x}_{adb_y}.png")
        self.adb.tap(self.device_id, adb_x, adb_y)
        self.adb.capture_screenshot(self.device_id, screenshot_path)
        ocr_text = self.ocr.extract_text(screenshot_path)
        cleaned = self.clean_ocr_text(ocr_text)
        return self.classify_node(cleaned)

    def store_data(self, adb_x: int, adb_y: int, x: int, y: int, node_type: str,
                   details: Dict[str, str], kingdom: Optional[str], kingdom_x: int, kingdom_y: int):
        details_json = json.dumps(details) if isinstance(details, dict) else str(details)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO grid_data (adb_x, adb_y, x, y, node_type, details, kingdom, kingdom_x, kingdom_y)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (adb_x, adb_y, x, y, node_type, details_json, kingdom, kingdom_x, kingdom_y),
            )
            conn.commit()
        env_id = f"{x},{y}"
        self.mcp.register_environment(env_id, {"type": node_type, "details": details, "kingdom": kingdom})

