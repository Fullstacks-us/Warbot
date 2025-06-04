import os
import json
from PIL import Image, ImageDraw, ImageFont
import logging


class AnnotationModule:
    def __init__(self, output_directory="annotations"):
        self.output_directory = output_directory
        os.makedirs(self.output_directory, exist_ok=True)
        self.logger = logging.getLogger("AnnotationModule")
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    def log_message(self, message, level=logging.INFO):
        """Log messages at the specified logging level."""
        self.logger.log(level, message)

    def annotate_image(self, image_path, annotations):
        """
        Annotate an image with bounding boxes and labels.

        Args:
            image_path (str): Path to the image to annotate.
            annotations (list): List of annotations, where each annotation is a dict with keys:
                - 'label': The label for the annotation.
                - 'bbox': A tuple (x_min, y_min, x_max, y_max) defining the bounding box.

        Returns:
            str: Path to the annotated image.
        """
        try:
            # Load the image
            image = Image.open(image_path)
            draw = ImageDraw.Draw(image)

            # Annotate the image with bounding boxes and labels
            for annotation in annotations:
                label = annotation.get("label", "Label")
                bbox = annotation.get("bbox", (0, 0, 10, 10))

                # Draw bounding box
                draw.rectangle(bbox, outline="red", width=2)

                # Add label text (handle long labels)
                text_position = (bbox[0], bbox[1] - 10)
                draw.text(text_position, label[:20], fill="red")

            # Save the annotated image
            filename = os.path.basename(image_path)
            output_path = os.path.join(self.output_directory, f"annotated_{filename}")
            image.save(output_path)
            self.log_message(f"Annotated image saved: {output_path}")
            return output_path

        except Exception as e:
            self.log_message(f"Failed to annotate image: {e}", level=logging.ERROR)
            raise RuntimeError(f"Failed to annotate image: {e}")

    def process_ocr_results(self, ocr_results):
        """
        Generate annotations from OCR results and annotate the corresponding images.

        Args:
            ocr_results (list): List of OCR results, where each result is a dict with keys:
                - 'filename': Name of the image file.
                - 'data': Dict containing:
                    - 'coordinates': List of dicts with keys 'x' and 'y'.
                    - 'raw_text': Extracted text.

        Returns:
            list: List of paths to annotated images.
        """
        annotated_paths = []

        try:
            for result in ocr_results:
                filename = result.get("filename")
                data = result.get("data", {})
                coordinates = data.get("coordinates", [])
                raw_text = data.get("raw_text", "")

                # Generate annotations
                annotations = []
                for coord in coordinates:
                    if isinstance(coord, dict) and "x" in coord and "y" in coord:
                        x = coord["x"]
                        y = coord["y"]
                        bbox = (x - 5, y - 5, x + 5, y + 5)  # Define bounding box
                        annotations.append({"label": "Point", "bbox": bbox})
                    else:
                        self.log_message(f"Invalid coordinate format: {coord}", level=logging.WARNING)

                # Annotate the image
                image_path = os.path.join("screenshots", filename)
                if os.path.exists(image_path):
                    annotated_path = self.annotate_image(image_path, annotations)
                    annotated_paths.append(annotated_path)
                else:
                    self.log_message(f"Image file not found: {image_path}", level=logging.ERROR)

            return annotated_paths

        except Exception as e:
            self.log_message(f"Failed to process OCR results: {e}", level=logging.ERROR)
            raise RuntimeError(f"Failed to process OCR results: {e}")


# Example Usage
if __name__ == "__main__":
    # Sample OCR results for testing
    ocr_results = [
        {
            "filename": "screenshot1.png",
            "data": {
                "coordinates": [{"x": 100, "y": 200}, {"x": 300, "y": 400}],
                "raw_text": "Example text"
            }
        },
        {
            "filename": "screenshot2.png",
            "data": {
                "coordinates": [{"x": 50, "y": 60}],
                "raw_text": "Another example"
            }
        }
    ]

    annotation_module = AnnotationModule(output_directory="test_annotations")

    try:
        annotated_images = annotation_module.process_ocr_results(ocr_results)
        print("Annotated Images:")
        for path in annotated_images:
            print(path)
    except RuntimeError as e:
        print(e)
