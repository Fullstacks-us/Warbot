import os
from PIL import Image, ImageDraw
import math
from adb_module import ADBModule  # Ensure you have an ADB module implemented
from ocr_module import OCRModule  # Ensure you have an OCR module implemented

class MapGridOverlay:
    def __init__(self, adb=None, ocr=None):
        self.adb = adb or ADBModule()
        self.ocr = ocr or OCRModule()

    def draw_rotated_grid(self, image_path, output_path, grid_width, grid_height, cell_size, rotation_angle, x_offset=0, y_offset=0, line_color="blue", line_width=2):
        """
        Overlay a rotated grid onto a screenshot.

        Args:
            image_path (str): Path to the input screenshot image.
            output_path (str): Path to save the output image with the grid overlay.
            grid_width (int): Number of cells horizontally in the grid.
            grid_height (int): Number of cells vertically in the grid.
            cell_size (int): Size of each cell in pixels.
            rotation_angle (float): Angle to rotate the grid in degrees.
            x_offset (int): Horizontal offset for the grid.
            y_offset (int): Vertical offset for the grid.
            line_color (str): Color of the grid lines.
            line_width (int): Thickness of the grid lines.
        """
        try:
            # Open the input image
            img = Image.open(image_path)
            overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)

            # Calculate the center of the image
            img_center_x = img.size[0] / 2
            img_center_y = img.size[1] / 2

            # Draw the grid lines
            for i in range(grid_width + 1):
                x_start = i * cell_size - (grid_width * cell_size / 2) + x_offset
                y_start = -img.size[1] / 2 + y_offset
                x_end = x_start
                y_end = img.size[1] / 2 + y_offset

                start_rotated = self.rotate_point(x_start, y_start, img_center_x, img_center_y, rotation_angle)
                end_rotated = self.rotate_point(x_end, y_end, img_center_x, img_center_y, rotation_angle)

                draw.line([start_rotated, end_rotated], fill=line_color, width=line_width)

            for j in range(grid_height + 1):
                x_start = -img.size[0] / 2 + x_offset
                y_start = j * cell_size - (grid_height * cell_size / 2) + y_offset
                x_end = img.size[0] / 2 + x_offset
                y_end = y_start

                start_rotated = self.rotate_point(x_start, y_start, img_center_x, img_center_y, rotation_angle)
                end_rotated = self.rotate_point(x_end, y_end, img_center_x, img_center_y, rotation_angle)

                draw.line([start_rotated, end_rotated], fill=line_color, width=line_width)

            # Calculate total number of grid cells
            total_cells = grid_width * grid_height
            draw.text((10, 10), f"Total Cells: {total_cells}", fill="red")

            # Combine the original image with the overlay
            img_with_overlay = Image.alpha_composite(img.convert("RGBA"), overlay)
            img_with_overlay = img_with_overlay.convert("RGB")

            # Save the output image
            img_with_overlay.save(output_path)
            print(f"Grid overlay saved to {output_path}")

        except Exception as e:
            print(f"Error creating grid overlay: {e}")

    def rotate_point(self, x, y, cx, cy, angle):
        """
        Rotate a point around a center point by a given angle.

        Args:
            x (float): X-coordinate of the point to rotate.
            y (float): Y-coordinate of the point to rotate.
            cx (float): X-coordinate of the center point.
            cy (float): Y-coordinate of the center point.
            angle (float): Rotation angle in degrees.

        Returns:
            tuple: Rotated (x, y) coordinates.
        """
        radians = math.radians(angle)
        cos_theta = math.cos(radians)
        sin_theta = math.sin(radians)

        # Translate point to origin
        x -= cx
        y -= cy

        # Rotate point
        x_rotated = x * cos_theta - y * sin_theta
        y_rotated = x * sin_theta + y * cos_theta

        # Translate point back
        x_rotated += cx
        y_rotated += cy

        return x_rotated, y_rotated

    def map_nodes(self, grid_width, grid_height, cell_size, rotation_angle, start_x, start_y):
        """
        Map nodes by tapping each grid cell, reading the popup, and logging coordinates.

        Args:
            grid_width (int): Number of grid cells horizontally.
            grid_height (int): Number of grid cells vertically.
            cell_size (int): Size of each cell in pixels.
            rotation_angle (float): Rotation angle of the grid.
            start_x (int): Starting X offset.
            start_y (int): Starting Y offset.
        """
        for row in range(grid_height):
            for col in range(grid_width):
                # Calculate the position to tap
                x = start_x + col * cell_size
                y = start_y + row * cell_size

                try:
                    # Tap the location
                    self.adb.tap(x, y)
                    print(f"Tapped on cell at ({x}, {y})")

                    # Wait for popup to appear
                    time.sleep(1)

                    # Read the popup using OCR
                    screenshot_path = "temp_screenshot.png"
                    self.adb.capture_screenshot(screenshot_path)
                    popup_text = self.ocr.read_text(screenshot_path)
                    print(f"Popup text: {popup_text}")

                    # Close the popup
                    self.adb.tap_close_button()
                    time.sleep(0.5)

                except Exception as e:
                    print(f"Error processing cell ({x}, {y}): {e}")

# Example usage
if __name__ == "__main__":
    grid_tool = MapGridOverlay()

    # Draw the grid overlay
    grid_tool.draw_rotated_grid(
        image_path="screenshots/emulator-5584_kingdom_914_x_255_y_483.png",
        output_path="adjusted_grid_overlay.png",
        grid_width=150,
        grid_height=150,
        cell_size=150,
        rotation_angle=45,
        x_offset=15,  # Adjust this for alignment
        y_offset=20,  # Adjust this for alignment
        line_color="blue",
        line_width=2
    )

    # Map nodes on the grid
    grid_tool.map_nodes(
        grid_width=10,
        grid_height=10,
        cell_size=150,
        rotation_angle=45,
        start_x=100,
        start_y=100
    )
