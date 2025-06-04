import os
import re
import csv
import logging
import tkinter as tk
from tkinter import NW
from PIL import Image, ImageTk
from ocr_module import OCRModule

ROI_LOG_FILE = "roi_log.csv"

def ensure_roi_log_header():
    """Create roi_log.csv with a header row if it doesn't exist."""
    if not os.path.isfile(ROI_LOG_FILE):
        with open(ROI_LOG_FILE, "w", encoding="utf-8") as f:
            f.write("original_filename,coord_box_left,coord_box_top,coord_box_right,coord_box_bottom,"
                    "type_box_left,type_box_top,type_box_right,type_box_bottom,"
                    "k_val,x_val,y_val,tile_type,new_filename\n")

def append_roi_log(original_filename, coord_box, type_box,
                   k_val=None, x_val=None, y_val=None, tile_type=None, new_filename=None):
    """
    Log the bounding boxes + extracted info to CSV.
    """
    (c_left, c_top, c_right, c_bottom) = coord_box
    (t_left, t_top, t_right, t_bottom) = type_box

    def safe_str(val):
        return val if val is not None else ""

    row = [
        original_filename,
        str(c_left), str(c_top), str(c_right), str(c_bottom),
        str(t_left), str(t_top), str(t_right), str(t_bottom),
        safe_str(k_val), safe_str(x_val), safe_str(y_val),
        safe_str(tile_type),
        safe_str(new_filename)
    ]

    with open(ROI_LOG_FILE, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(row)

def select_crop_region(image_path, prompt_title="Select Crop Region"):
    """
    Opens a GUI with the image, lets the user drag a rectangle to define the crop region.
    Returns (left, top, right, bottom) or None if invalid.
    """
    root = tk.Tk()
    root.title(prompt_title)

    pil_img = Image.open(image_path)
    width, height = pil_img.size
    tk_img = ImageTk.PhotoImage(pil_img)

    canvas = tk.Canvas(root, width=width, height=height, cursor="cross")
    canvas.pack()
    canvas.create_image(0, 0, anchor=NW, image=tk_img)

    start_x, start_y = [0, 0]
    rect_id = None
    crop_box = None

    def on_mouse_down(event):
        nonlocal start_x, start_y, rect_id
        start_x, start_y = event.x, event.y
        if rect_id is not None:
            canvas.delete(rect_id)
        rect_id = canvas.create_rectangle(
            start_x, start_y, start_x, start_y,
            outline="red", width=2
        )

    def on_mouse_move(event):
        if rect_id is not None:
            canvas.coords(rect_id, start_x, start_y, event.x, event.y)

    def on_mouse_up(event):
        nonlocal crop_box
        x1, y1 = start_x, start_y
        x2, y2 = event.x, event.y
        # Ensure left < right, top < bottom
        if x2 < x1:
            x1, x2 = x2, x1
        if y2 < y1:
            y1, y2 = y2, y1

        # Minimal box size
        if (x2 - x1) > 2 and (y2 - y1) > 2:
            crop_box = (x1, y1, x2, y2)
        else:
            crop_box = None
        root.quit()

    canvas.bind("<ButtonPress-1>", on_mouse_down)
    canvas.bind("<B1-Motion>", on_mouse_move)
    canvas.bind("<ButtonRelease-1>", on_mouse_up)

    root.mainloop()
    try:
        root.destroy()
    except tk.TclError:
        pass

    return crop_box

def detect_tile_type(ocr_text):
    """
    Simple logic to classify tile type based on keywords in OCR text.
    Adjust to match your actual game terms. 
    """

    text_lower = ocr_text.lower()

    # Monster
    if any(keyword in text_lower for keyword in ["monster hunt", "dmg", "monster"]):
        return "monster"

    # Resource
    if any(keyword in text_lower for keyword in [
        "gather", "field", "timber", "rich vein", "rocks", "occupier", 
        "wood", "ore", "stone", "food", "gold", "ruins"
    ]):
        return "rss"

    # Vacant
    if any(keyword in text_lower for keyword in [
        "transfer", "forest", "magma path", 
        "grassland", "mountain", "shore", "sea", 
        "volcano", "lava hill", "glacier"
    ]):
        return "vacant"

    # Darknest (check first if you specifically see "darknest" in the text)
    if "darknest" in text_lower:
        return "darknest"

    # Castle
    # Here we also include "scout", "rally attack", "attack", etc. 
    # because many castle/darknest screens are similar. But "darknest"
    # is specifically matched above if "darknest" is found in text_lower.
    if any(keyword in text_lower for keyword in [
        "scout", "rally attack", "attack", "troops killed:",
        "might:", "guild:", "kingdom:", "view profile", "enter turf"
    ]):
        return "castle"

    return "unknown"

def main():
    """
    For each .png in 'screenshots/':
    1) User selects two bounding boxes:
       - Box A: where K: X: Y: is found.
       - Box B: where tile-type text is found (e.g. "Attack", "Gather", etc.).
    2) OCR both cropped images, combine text.
    3) Regex out K, X, Y; detect tile type from keywords.
    4) Rename the file accordingly.
    5) Log everything to roi_log.csv.
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger("ScreenshotDoubleCrop")

    ocr = OCRModule()
    coords_pattern = re.compile(r"K\s*:\s*(\d+).*?X\s*:\s*(\d+).*?Y\s*:\s*(\d+)", re.IGNORECASE | re.DOTALL)

    # Make sure roi_log.csv has a header
    ensure_roi_log_header()

    screenshots_dir = "screenshots"
    if not os.path.isdir(screenshots_dir):
        logger.error(f"Directory '{screenshots_dir}' does not exist.")
        return

    files = [f for f in os.listdir(screenshots_dir) if f.lower().endswith(".png")]
    for filename in files:
        original_path = os.path.join(screenshots_dir, filename)
        logger.info(f"Processing {filename} ...")

        # 1) Ask user for bounding boxes
        logger.info("Select coordinate region (K: X: Y:).")
        coord_box = select_crop_region(original_path, prompt_title="Select Coordinates Region")
        if not coord_box:
            logger.warning("No valid coordinate region selected; skipping file.")
            append_roi_log(filename, (0,0,0,0), (0,0,0,0))
            continue

        logger.info("Select tile-type region (Monster/Resource/etc.).")
        type_box = select_crop_region(original_path, prompt_title="Select Tile-Type Region")
        if not type_box:
            logger.warning("No valid tile-type region selected; skipping file.")
            append_roi_log(filename, coord_box, (0,0,0,0))
            continue

        # 2) Crop & OCR
        coord_crop_path = os.path.join(screenshots_dir, "temp_coord_crop.png")
        type_crop_path = os.path.join(screenshots_dir, "temp_type_crop.png")

        def safe_crop_and_ocr(crop_box_local, input_path, output_path):
            # Crop image to 'crop_box_local' and run OCR, or return "" on error
            try:
                from PIL import Image
                with Image.open(input_path) as img:
                    w, h = img.size
                    (cx1, cy1, cx2, cy2) = crop_box_local
                    # Validate bounds
                    if cx1 < 0 or cy1 < 0 or cx2 > w or cy2 > h:
                        return ""
                    cropped_img = img.crop(crop_box_local)
                    cropped_img.save(output_path)
            except Exception as e:
                logger.error(f"Failed to crop '{filename}' box {crop_box_local}: {e}")
                return ""

            text = ocr.extract_text(output_path)
            # Clean up
            if os.path.exists(output_path):
                os.remove(output_path)
            return text or ""

        coord_text = safe_crop_and_ocr(coord_box, original_path, coord_crop_path)
        type_text = safe_crop_and_ocr(type_box, original_path, type_crop_path)

        combined_text = coord_text + "\n" + type_text
        if not combined_text.strip():
            logger.warning("No text recognized from either crop; skipping rename.")
            append_roi_log(filename, coord_box, type_box)
            continue

        # 3) Parse Coordinates
        match = coords_pattern.search(combined_text)
        if not match:
            logger.info(f"No coordinates found in '{filename}'.\nOCR text:\n{combined_text}")
            append_roi_log(filename, coord_box, type_box)
            continue
        k_val, x_val, y_val = match.groups()

        # 4) Detect Tile Type
        tile_type = detect_tile_type(combined_text)
        logger.info(f"Detected tile type: {tile_type}")

        # 5) Rename File
        new_filename = f"K_{k_val}_X_{x_val}_Y_{y_val}_{tile_type}.png"
        new_path = os.path.join(screenshots_dir, new_filename)
        try:
            os.rename(original_path, new_path)
            logger.info(f"Renamed '{filename}' -> '{new_filename}'")
            append_roi_log(filename, coord_box, type_box, k_val, x_val, y_val, tile_type, new_filename)
        except Exception as e:
            logger.error(f"Failed to rename '{filename}' to '{new_filename}': {e}")
            append_roi_log(filename, coord_box, type_box, k_val, x_val, y_val, tile_type)

if __name__ == "__main__":
    main()
