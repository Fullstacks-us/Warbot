import os
import cv2
import numpy as np
import logging
from adb_module2 import ADBModule  # Assuming ADBModule is in the project folder
import json


class TemplateMatchingModule:
    def __init__(self, templates_dir="templates", output_dir="output"):
        self.templates_dir = templates_dir
        self.output_dir = output_dir
        self.adb = ADBModule()
        self.logger = logging.getLogger("TemplateMatchingModule")
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        os.makedirs(self.output_dir, exist_ok=True)

        # Load metadata for organized templates
        self.metadata_file = os.path.join(self.templates_dir, "metadata.json")
        self.templates_metadata = self._load_metadata()
        self.validate_metadata()

    def _load_metadata(self):
        """Load metadata for templates."""
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, "r") as f:
                return json.load(f)
        else:
            self.log_message(f"Metadata file not found. Starting with an empty metadata dictionary.", level=logging.WARNING)
            return {}

    def validate_metadata(self):
        """Validate and clean metadata to ensure templates exist."""
        cleaned_metadata = {}
        for category, levels in self.templates_metadata.items():
            for level, details in levels.items():
                template_path = os.path.join(self.templates_dir, f"{category}_{level}.png")
                if os.path.exists(template_path):
                    cleaned_metadata.setdefault(category, {})[level] = details
                else:
                    self.log_message(f"Removing invalid entry for {category} level {level}", level=logging.WARNING)
        self.templates_metadata = cleaned_metadata
        with open(self.metadata_file, "w") as f:
            json.dump(cleaned_metadata, f, indent=4)
        self.log_message("Metadata validated and cleaned.")

    def log_message(self, message, level=logging.INFO):
        """Log messages at the specified logging level."""
        self.logger.log(level, message)

    def debug_templates(self):
        """List template files and compare with metadata."""
        all_files = os.listdir(self.templates_dir)
        self.log_message("Files in templates directory:")
        for file in all_files:
            self.log_message(f" - {file}")
        self.log_message("\nMetadata entries:")
        for category, levels in self.templates_metadata.items():
            for level in levels:
                self.log_message(f" - {category}_{level}.png")

    def load_templates(self):
        """
        Load categorized templates based on metadata.

        Returns:
            dict: Dictionary with templates categorized by type and level.
        """
        templates = {}
        for category, levels in self.templates_metadata.items():
            templates[category] = {}
            for level, details in levels.items():
                template_path = os.path.join(self.templates_dir, f"{category}_{level}.png")
                if not os.path.exists(template_path):
                    self.log_message(f"Template file not found: {template_path}", level=logging.WARNING)
                    continue

                template_image = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
                if template_image is not None:
                    templates[category][level] = template_image
                else:
                    self.log_message(f"Failed to load template: {template_path}", level=logging.WARNING)
        return templates

    def non_max_suppression(self, matches, overlap_thresh=0.5):
        """
        Perform Non-Maximum Suppression (NMS) on matches to remove duplicates.

        Args:
            matches (list): List of matches with their positions and dimensions.
            overlap_thresh (float): Threshold for overlap. Defaults to 0.5.

        Returns:
            list: Filtered matches after NMS.
        """
        if not matches:
            return []

        # Convert matches to numpy array
        boxes = np.array([[match["position"][0], match["position"][1],
                            match["position"][0] + match["dimensions"][0],
                            match["position"][1] + match["dimensions"][1]] for match in matches])

        indices = np.arange(len(boxes))
        pick = []

        # Coordinates of boxes
        x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
        area = (x2 - x1) * (y2 - y1)
        idxs = np.argsort(y2)  # Sort by bottom-right y-coordinate

        while len(idxs) > 0:
            last = idxs[-1]
            pick.append(last)

            # Compare this box to all others
            xx1 = np.maximum(x1[last], x1[idxs[:-1]])
            yy1 = np.maximum(y1[last], y1[idxs[:-1]])
            xx2 = np.minimum(x2[last], x2[idxs[:-1]])
            yy2 = np.minimum(y2[last], y2[idxs[:-1]])

            # Calculate overlap
            w = np.maximum(0, xx2 - xx1)
            h = np.maximum(0, yy2 - yy1)
            overlap = (w * h) / area[idxs[:-1]]

            idxs = idxs[np.where(overlap <= overlap_thresh)[0]]

        return [matches[i] for i in pick]

    def match_templates(self, screenshot_path, threshold_config=None, nms_threshold=0.5):
        """
        Match all templates against the given screenshot.

        Args:
            screenshot_path (str): Path to the screenshot.
            threshold_config (dict): Optional threshold configuration by category.
            nms_threshold (float): Overlap threshold for Non-Maximum Suppression.

        Returns:
            list: List of matches with their coordinates, dimensions, category, level, and landscape.
        """
        try:
            screenshot = cv2.imread(screenshot_path, cv2.IMREAD_GRAYSCALE)
            if screenshot is None:
                raise RuntimeError("Failed to load screenshot.")

            templates = self.load_templates()
            matches = []

            for category, levels in templates.items():
                threshold = threshold_config.get(category, 0.8) if threshold_config else 0.8
                for level, template in levels.items():
                    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
                    locations = np.where(result >= threshold)
                    for pt in zip(*locations[::-1]):
                        matches.append({
                            "template": f"{category}_{level}",
                            "category": category,
                            "level": level,
                            "position": pt,
                            "dimensions": (template.shape[1], template.shape[0])  # (width, height)
                        })
                        self.log_message(f"Match found for {category} (level {level}) at {pt}")

            filtered_matches = self.non_max_suppression(matches, overlap_thresh=nms_threshold)
            self.log_message(f"Matches after NMS: {len(filtered_matches)}")
            return filtered_matches
        except Exception as e:
            raise RuntimeError(f"Template matching failed: {e}")

    def draw_matches(self, screenshot_path, matches, output_path):
        """
        Draw rectangles around matches on the screenshot and save the result.

        Args:
            screenshot_path (str): Path to the screenshot.
            matches (list): List of matches with coordinates and dimensions.
            output_path (str): Path to save the marked screenshot.
        """
        try:
            screenshot = cv2.imread(screenshot_path)
            for match in matches:
                x, y = match["position"]
                w, h = match["dimensions"]
                cv2.rectangle(screenshot, (x, y), (x + w, y + h), (0, 0, 255), 2)  # Red rectangle
                label = f"{match['category']} L{match['level']}"
                cv2.putText(screenshot, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                self.log_message(f"Marked {label} at ({x}, {y})")

            cv2.imwrite(output_path, screenshot)
            self.log_message(f"Marked screenshot saved to {output_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to draw matches: {e}")

    def scan_and_mark(self, device_id, threshold_config=None):
        """
        Capture a screenshot, match templates, and save an image with matches marked.

        Args:
            device_id (str): The ID of the target device.
            threshold_config (dict): Optional threshold configuration by category.
        """
        try:
            # Capture screenshot
            screenshot_path = f"screenshots/{device_id}_screenshot.png"
            self.adb.capture_screenshot(device_id, save_path=screenshot_path)

            # Match templates
            matches = self.match_templates(screenshot_path, threshold_config=threshold_config)
            if not matches:
                self.log_message("No matches found.")
                return

            # Draw matches and save marked screenshot
            output_path = os.path.join(self.output_dir, f"{device_id}_marked.png")
            self.draw_matches(screenshot_path, matches, output_path)

        except Exception as e:
            raise RuntimeError(f"Failed to scan and mark: {e}")


# Example usage
if __name__ == "__main__":
    template_matching = TemplateMatchingModule()

    # Debug template files and metadata
    template_matching.debug_templates()

    # Example device ID (replace with an actual device ID)
    device_id = "emulator-5554"

    # Threshold configuration (optional)
    threshold_config = {
        "Darknests": 0.9,
        "Food": 0.8,
        "Castles": 0.75
    }

    # Perform template matching and mark matches
    try:
        template_matching.scan_and_mark(device_id, threshold_config=threshold_config)
    except RuntimeError as e:
        print(e)
