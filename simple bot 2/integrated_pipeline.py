import os
import logging
from ocr_module import OCRModule
from annotation_module import AnnotationModule


class Pipeline:
    def __init__(self, input_dir="screenshots", output_dir="annotations"):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.ocr_module = OCRModule()
        self.annotation_module = AnnotationModule(output_directory=self.output_dir)

        # Set up logging
        self.logger = logging.getLogger("Pipeline")
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    def log_message(self, message, level=logging.INFO):
        """Log messages at the specified logging level."""
        self.logger.log(level, message)

    def rename_files(self):
        """
        Renames files in the input directory to `screenshot.png`, `screenshot1.png`, etc., avoiding name conflicts.

        Returns:
            list: List of renamed file paths.
        """
        try:
            files = [
                f for f in os.listdir(self.input_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))
            ]
            renamed_files = []

            # Maintain a set of existing filenames to avoid overwriting
            existing_filenames = set(os.listdir(self.input_dir))

            for idx, filename in enumerate(files):
                original_path = os.path.join(self.input_dir, filename)
                renamed_filename = f"screenshot{'' if idx == 0 else idx}.png"

                # Ensure unique filename
                while renamed_filename in existing_filenames:
                    idx += 1
                    renamed_filename = f"screenshot{idx}.png"

                renamed_path = os.path.join(self.input_dir, renamed_filename)

                # Rename the file
                os.rename(original_path, renamed_path)
                renamed_files.append(renamed_path)
                existing_filenames.add(renamed_filename)  # Track renamed filenames
                self.log_message(f"Renamed {filename} to {renamed_filename}")

            return renamed_files
        except Exception as e:
            self.log_message(f"Failed to rename files: {e}", level=logging.ERROR)
            raise RuntimeError(f"Failed to rename files: {e}")

    def process_pipeline(self):
        """
        Runs the full pipeline:
        1. Rename files in the input directory.
        2. Perform OCR on renamed files.
        3. Annotate images based on OCR results.
        """
        try:
            # Step 1: Rename files
            self.log_message("Starting file renaming...")
            renamed_files = self.rename_files()

            if not renamed_files:
                self.log_message("No images found to process.", level=logging.WARNING)
                return

            # Step 2: Perform OCR
            self.log_message("Starting OCR processing...")
            ocr_results = self.ocr_module.batch_process(self.input_dir)

            if not ocr_results:
                self.log_message("OCR processing returned no results.", level=logging.WARNING)
                return

            # Step 3: Annotate Images
            self.log_message("Starting annotation...")
            annotated_paths = self.annotation_module.process_ocr_results(ocr_results)

            self.log_message("Pipeline completed successfully!")
            self.log_message("Annotated Images:")
            for path in annotated_paths:
                self.log_message(path)

        except Exception as e:
            self.log_message(f"Pipeline execution failed: {e}", level=logging.ERROR)


# Example Usage
if __name__ == "__main__":
    pipeline = Pipeline(input_dir="screenshots", output_dir="annotations")
    pipeline.process_pipeline()
