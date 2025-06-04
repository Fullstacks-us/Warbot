import os
from ocr_module import OCRModule

def test_ocr_module():
    """
    Test the OCRModule with single and batch image processing.
    """
    # Initialize OCRModule
    ocr = OCRModule()

    # Set up directories and test files
    test_images_dir = "test_images"
    os.makedirs(test_images_dir, exist_ok=True)

    # Ensure there are some test images
    if not os.listdir(test_images_dir):
        print(f"No test images found in {test_images_dir}. Please add test images.")
        return

    print("Starting OCR tests...")

    # Test single image processing
    try:
        test_image = os.path.join(test_images_dir, os.listdir(test_images_dir)[0])
        print(f"Testing single image OCR on: {test_image}")

        text = ocr.extract_text(test_image)
        print("Extracted Text:")
        print(text)

        structured_data = ocr.extract_structured_data(test_image)
        print("Structured Data:")
        print(structured_data)

    except RuntimeError as e:
        print(f"Single image OCR test failed: {e}")

    # Test batch image processing
    try:
        print("\nTesting batch OCR processing...")
        batch_results = ocr.batch_process(test_images_dir)
        print("Batch OCR Results:")
        for result in batch_results:
            print(result)

    except RuntimeError as e:
        print(f"Batch OCR test failed: {e}")

if __name__ == "__main__":
    test_ocr_module()
