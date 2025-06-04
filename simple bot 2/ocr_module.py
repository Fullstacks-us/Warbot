import logging
import pytesseract
from PIL import Image

class OCRModule:
    def __init__(self):
        self.logger = logging.getLogger("OCRModule")
        self._setup_logging()

    def _setup_logging(self):
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def extract_text(self, image_path):
        """
        Uses Tesseract (pytesseract) to extract text from `image_path`.
        Returns a string of recognized text.
        """
        self.logger.info(f"OCR on {image_path}")
        try:
            with Image.open(image_path) as img:
                text = pytesseract.image_to_string(img)
            return text
        except Exception as e:
            self.logger.error(f"Failed to perform OCR on {image_path}. Error: {e}")
            return ""
