import unittest
from unittest.mock import MagicMock
import os
import sqlite3
from nodemapper import NodeMapper


class TestNodeMapper(unittest.TestCase):
    def setUp(self):
        # Mock ADB and OCR modules
        self.adb_mock = MagicMock()
        self.ocr_mock = MagicMock()

        # Initialize NodeMapper with mocks
        self.mapper = NodeMapper(adb=self.adb_mock, ocr=self.ocr_mock, device_id="test-emulator")

        # Ensure directories exist for screenshots and raw_text
        os.makedirs("screenshots", exist_ok=True)
        os.makedirs("raw_text", exist_ok=True)

        # Example OCR text and expected classifications
        self.test_cases = [
            {
                "ocr_text": "Might: 76,557,357 Troops Killed: 93,109 Guild: PXU Kingdom: Teyagia",
                "expected_node_type": "Castle",
            },
            {
                "ocr_text": "Grass1and Kingdom of Teyagia Transfer Occupy",
                "expected_node_type": "Grassland",
            },
            {
                "ocr_text": "Vacant Spot Available for Occupy",
                "expected_node_type": "Vacant",
            },
            {
                "ocr_text": "Darknest Level 2 - Attack Now!",
                "expected_node_type": "Darknest",
            },
            {
                "ocr_text": "Some random unrecognizable text",
                "expected_node_type": "Unknown",
            },
        ]

    def tearDown(self):
        """Clean up test directories and files."""
        for dir_name in ["screenshots", "raw_text"]:
            if os.path.exists(dir_name):
                for file in os.listdir(dir_name):
                    file_path = os.path.join(dir_name, file)
                    try:
                        os.remove(file_path)
                    except PermissionError:
                        print(f"Permission denied while deleting file: {file_path}")

    def test_classify_node(self):
        """Test node classification based on OCR text."""
        self.test_cases = [
            {
                "ocr_text": "Darknest Level 2\nMight: 123,456\nRequires min. 2-player Rally\nScout\nRally Attack\nK: 123 X: 456 Y: 789",
                "expected_node_type": "Darknest",
            },
            {
                "ocr_text": "[PXU] PlayerName\nMight: 876,543\nTroops Killed: 12,345\nGuild: PXU\nKingdom: Teyagia\nView Profile\nRally Attack",
                "expected_node_type": "Castle",
            },
            {
                "ocr_text": "Grassland\nTransfer\nOccupy\nK: 123 X: 456 Y: 789",
                "expected_node_type": "Vacant",
            },
            {
                "ocr_text": "Rich Vein Lv. 2\nTransfer\nOccupy\nK: 123 X: 456 Y: 789",
                "expected_node_type": "Rss Tile",
            },
            {
                "ocr_text": "Level 5 Gargantua\nDeal extra DMG when you hunt the same monster in succession\nDMG Boost x2",
                "expected_node_type": "Monster",
            },
        ]

        for case in self.test_cases:
            with self.subTest(ocr_text=case["ocr_text"]):
                # Simulate OCR text
                cleaned_text = self.mapper.clean_ocr_text(case["ocr_text"])

                # Classify the node
                node_type, _, _ = self.mapper.classify_node(cleaned_text)

                # Assert node type matches expected result
                self.assertEqual(node_type, case["expected_node_type"])


    def test_process_node(self):
        """Test full node processing."""
        adb_x, adb_y = 100, 200
        ocr_text = "Grass1and Kingdom of Teyagia Transfer Occupy"
        expected_node_type = "Grassland"

        # Mock ADB and OCR behavior
        self.adb_mock.tap.return_value = True
        self.ocr_mock.extract_text.return_value = ocr_text

        # Process the node
        self.mapper.process_node(adb_x, adb_y)

        # Check ADB commands were called
        self.adb_mock.tap.assert_called_with("test-emulator", adb_x, adb_y)
        self.adb_mock.capture_screenshot.assert_called_with(
            "test-emulator", os.path.join("screenshots", f"node_{adb_x}_{adb_y}.png")
        )

        # Verify OCR text is classified correctly
        cleaned_text = self.mapper.clean_ocr_text(ocr_text)
        node_type, _, _ = self.mapper.classify_node(cleaned_text)
        self.assertEqual(node_type, expected_node_type)

    def test_store_data(self):
        """Test storing data into the database."""
        adb_x, adb_y = 69, 183
        x, y = 0, 0
        node_type = "Castle"
        details = {"guild": "PXU", "might": "76,557,357", "troops_killed": "93,109"}
        kingdom = "Teyagia"
        kingdom_x, kingdom_y = 263, 0

        # Store data
        self.mapper.store_data(adb_x, adb_y, x, y, node_type, details, kingdom, kingdom_x, kingdom_y)

        # Query the database to check the record
        with sqlite3.connect(self.mapper.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM grid_data WHERE adb_x = ? AND adb_y = ?", (adb_x, adb_y))
            row = cursor.fetchone()

        # Assert the row matches the stored data
        self.assertIsNotNone(row)
        self.assertEqual(row[0], adb_x)  # adb_x
        self.assertEqual(row[1], adb_y)  # adb_y
        self.assertEqual(row[4], node_type)  # node_type

    def test_clean_ocr_text(self):
        """Test OCR text cleaning."""
        raw_text = "¥Vacant One Spot! | K:263  X:1  Y:7\nTransfer"
        cleaned_text = self.mapper.clean_ocr_text(raw_text)
        expected_text = "Vacant One Spot! K:263 X:1 Y:7 Transfer"

        # Assert that the cleaned text matches expected output
        self.assertEqual(cleaned_text, expected_text)


if __name__ == "__main__":
    unittest.main()
