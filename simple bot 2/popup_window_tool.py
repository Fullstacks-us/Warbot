import tkinter as tk
from tkinter import filedialog, simpledialog  # Add simpledialog import
import cv2
import os
import json
from PIL import Image, ImageTk
from adb_module import ADBModule  # Your provided ADB module


class PopupWindowTool:
    def __init__(self, device_id="emulator-5554"):
        self.root = tk.Tk()
        self.root.title("Popup Window ROI Selector")

        self.canvas = tk.Canvas(self.root, cursor="cross")
        self.canvas.pack(fill="both", expand=True)

        self.image = None
        self.photo_image = None
        self.start_x = self.start_y = None
        self.rect_id = None
        self.device_id = device_id
        self.adb = ADBModule()  # Initialize ADB module

        self.result = None

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        self.capture_button = tk.Button(self.root, text="Capture Screenshot", command=self.capture_image)
        self.capture_button.pack(side="left")

        self.save_button = tk.Button(self.root, text="Save ROI", command=self.save_roi, state="disabled")
        self.save_button.pack(side="left")

        self.quit_button = tk.Button(self.root, text="Quit", command=self.root.quit)
        self.quit_button.pack(side="right")

        self.roi = None

    def capture_image(self):
        """
        Capture a screenshot from the connected device using ADB.
        """
        screenshot_path = "temp_screenshot.png"
        try:
            # Capture screenshot from the device
            self.adb.capture_screenshot(self.device_id, screenshot_path)
            print(f"Screenshot captured and saved to {screenshot_path}")

            # Load the captured screenshot
            self.image = cv2.imread(screenshot_path)
            self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
            self.display_image()
        except Exception as e:
            print(f"Error capturing screenshot: {e}")

    def display_image(self):
        """
        Display the loaded screenshot on the canvas.
        """
        self.photo_image = ImageTk.PhotoImage(Image.fromarray(self.image))
        self.canvas.create_image(0, 0, image=self.photo_image, anchor=tk.NW)

    def on_button_press(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.rect_id = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="red", width=2)

    def on_mouse_drag(self, event):
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, event.x, event.y)

    def on_button_release(self, event):
        end_x, end_y = event.x, event.y
        self.roi = (min(self.start_x, end_x), min(self.start_y, end_y), max(self.start_x, end_x), max(self.start_y, end_y))
        print(f"Selected ROI: {self.roi}")
        self.save_button["state"] = "normal"

    def save_roi(self):
        if self.roi and self.image is not None:
            x1, y1, x2, y2 = self.roi
            node_type = tk.simpledialog.askstring("Node Type", "Enter Node Type (e.g., Castle, Monster):")
            if not node_type:
                print("Node type is required to save ROI.")
                return

            config_path = "roi_config.json"
            roi_data = {}

            # Load existing ROI data
            if os.path.exists(config_path):
                with open(config_path, "r") as file:
                    roi_data = json.load(file)

            # Add or update the ROI for the node type
            roi_data[node_type] = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}

            # Save updated ROI data
            with open(config_path, "w") as file:
                json.dump(roi_data, file, indent=4)
                print(f"ROI for '{node_type}' saved to {config_path}")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    tool = PopupWindowTool(device_id="emulator-5554")
    tool.run()
