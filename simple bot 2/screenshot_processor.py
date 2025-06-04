# screenshot_processor.py

import os
import re
from typing import Optional, Tuple
from PIL import Image, ImageOps
import pytesseract
import cv2
import numpy as np

class ScreenshotProcessor:
    """
    Extracts:
      1) 'view center' coords from a known bounding box
      2) 'clicked tile' coords by checking multiple possible ROIs.
         E.g., castle/darknest ROI, monster ROI, resource tile ROI, vacant tile ROI.
      3) Detects pop-up presence via template matching of the Close button.
    """

    # Regex for full "K, X, Y"
    FULL_COORD_REGEX = re.compile(
        r"K\s*[:=]?\s*(\d{1,5})\s*X\s*[:=]?\s*(\d{1,5})\s*Y\s*[:=]?\s*(\d{1,5})",
        re.IGNORECASE
    )
    # Fallback for "X:#### Y:####" if K is missing
    XY_COORD_REGEX = re.compile(
        r"X\s*[:=]?\s*(\d{1,5})\s*Y\s*[:=]?\s*(\d{1,5})",
        re.IGNORECASE
    )

    def __init__(self, template_path='templates/close_button.png'):
        # Load the Close button template once during initialization
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Close button template not found at {template_path}")

        template_image = Image.open(template_path).convert('L')  # Grayscale
        self.close_button_np = np.array(template_image)
        self.template_width, self.template_height = template_image.size

    def extract_text_from_roi(self, image_path: str, roi: Tuple[int, int, int, int]) -> str:
        """Crop image to ROI, optionally preprocess, run OCR, return text."""
        if not os.path.exists(image_path):
            print(f"[WARN] Image not found: {image_path}")
            return ""

        try:
            with Image.open(image_path) as img:
                cropped = img.crop(roi).convert("L")
                # Optional: Apply thresholding to improve OCR accuracy
                # cropped = cropped.point(lambda x: 0 if x < 128 else 255, '1')
                text = pytesseract.image_to_string(cropped).strip()
            print(f"[DEBUG] OCR from ROI {roi}: {text}")
            return text
        except Exception as e:
            print(f"[ERROR] {e}")
            return ""

    def parse_coordinates(self, text: str) -> Optional[Tuple[Optional[int], Optional[int], Optional[int]]]:
        """
        1. Try FULL_COORD_REGEX for 'K, X, Y'.
        2. If not found, fallback to XY_COORD_REGEX for 'X, Y' (K= None).
        Returns (K, X, Y) or (None, X, Y), or None if no match.
        """
        m_full = self.FULL_COORD_REGEX.search(text)
        if m_full:
            try:
                k_str, x_str, y_str = m_full.groups()
                return (int(k_str), int(x_str), int(y_str))
            except ValueError:
                pass

        m_xy = self.XY_COORD_REGEX.search(text)
        if m_xy:
            try:
                x_str, y_str = m_xy.groups()
                return (None, int(x_str), int(y_str))
            except ValueError:
                pass

        return None

    def find_close_button(self, image_path: str) -> Optional[Tuple[int, int]]:
        """
        Detects the Close button in the screenshot using template matching.
        Checks two known positions:
          - (1075, 160)
          - (1540, 60)
        Returns the position where the Close button was found, or None.
        """
        if not os.path.exists(image_path):
            print(f"[WARN] Image not found: {image_path}")
            return None

        try:
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                print(f"[ERROR] Failed to read image: {image_path}")
                return None

            # Define the two close button positions
            close_button_positions = [
                (1075, 160),
                (1540, 60)
            ]

            # Define a small window around each position to search
            search_window_size = (100, 100)  # width, height

            # Define a similarity threshold
            threshold = 0.8

            for pos in close_button_positions:
                x, y = pos
                w, h = self.template_width, self.template_height

                # Define the ROI around the close button position
                x1 = max(x - search_window_size[0]//2, 0)
                y1 = max(y - search_window_size[1]//2, 0)
                x2 = min(x + search_window_size[0]//2, img.shape[1])
                y2 = min(y + search_window_size[1]//2, img.shape[0])

                roi = img[y1:y2, x1:x2]

                # Perform template matching
                res = cv2.matchTemplate(roi, self.close_button_np, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

                print(f"[DEBUG] Template match at position {pos}: similarity={max_val}")

                if max_val >= threshold:
                    # Close button found at this position
                    print(f"[INFO] Close button detected at position {pos} with similarity {max_val}")
                    return pos

            # Close button not found
            print("[INFO] No close button detected in the known positions.")
            return None

        except Exception as e:
            print(f"[ERROR] Exception in find_close_button: {e}")
            return None

    def get_view_center_coords(
        self, image_path: str, roi_center: Tuple[int, int, int, int]
    ) -> Optional[Tuple[Optional[int], Optional[int], Optional[int]]]:
        """
        Extract 'view center' coords from the known bounding box.
        """
        text_center = self.extract_text_from_roi(image_path, roi_center)
        return self.parse_coordinates(text_center)

    def get_clicked_tile_coords(self, image_path: str, roi: Tuple[int, int, int, int]) -> Optional[Tuple[Optional[int], Optional[int], Optional[int]]]:
        """OCR a single ROI for the 'clicked tile' coords."""
        text_popup = self.extract_text_from_roi(image_path, roi)
        return self.parse_coordinates(text_popup)

    def process_screenshot(
        self,
        screenshot_path: str,
        roi_center: Tuple[int, int, int, int],
        roi_popup_castle_darknest: Optional[Tuple[int, int, int, int]] = None,
        roi_popup_monster: Optional[Tuple[int, int, int, int]] = None,
        roi_popup_rss_tile: Optional[Tuple[int, int, int, int]] = None,
        roi_popup_vacant_tile: Optional[Tuple[int, int, int, int]] = None,
    ) -> Tuple[Optional[Tuple[Optional[int], Optional[int], Optional[int]]], Optional[Tuple[Optional[int], Optional[int], Optional[int]]]]:
        """
        Returns:
          (center_coords, clicked_coords)
          center_coords -> (K, X, Y) or (None, X, Y) or None
          clicked_coords -> first successful parse from any of the 4 popup ROIs
        """
        # 1) OCR for center tile
        center_coords = self.get_view_center_coords(screenshot_path, roi_center)

        # 2) OCR for clicked tile: check each possible ROI in turn
        # The first one that yields valid coords is returned. If none match, it's None.
        clicked_coords = None
        popup_rois = [
            roi_popup_castle_darknest,
            roi_popup_monster,
            roi_popup_rss_tile,
            roi_popup_vacant_tile
        ]
        for roi in popup_rois:
            if roi is None:
                continue
            coords = self.get_clicked_tile_coords(screenshot_path, roi)
            if coords:
                clicked_coords = coords
                break

        return center_coords, clicked_coords
