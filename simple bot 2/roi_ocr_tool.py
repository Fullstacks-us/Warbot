import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import json
import os

class ROISelector:
    def __init__(self, master, roi_file="rois.json"):
        self.master = master
        self.master.title("ROI Selector")
        self.canvas = tk.Canvas(master, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.roi_file = roi_file
        self.image = None
        self.tk_image = None

        self.all_rois = {
            "tile_scanning": [],
            "popups": [],
            "ocr_regions": [],
            "center_tile": [],
            "tile_coordinates": [],
            "guild": [],
            "might": [],
            "troops_killed": [],
            "resource_type": [],
            "occupier": [],
            "castle_name": [],
            "node_types": { "castle": [], "darknest": [], "monster": [], "resource": [], "vacant": [] }
        }
        self.current_roi_type = "tile_scanning"
        self.rectangles = []
        self.rect_ids = []
        self.start_x = None
        self.start_y = None
        self.rect_id = None

        file_path = filedialog.askopenfilename(
            title="Select Map Screenshot",
            filetypes=[("Image files", "*.png *.jpg *.jpeg")]
        )

        if not file_path:
            print("❌ No file selected. Exiting.")
            self.master.destroy()
            return

        self.image = Image.open(file_path)
        self.tk_image = ImageTk.PhotoImage(self.image)

        self.canvas.config(width=self.tk_image.width(), height=self.tk_image.height())
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

        self.load_existing_rois()

        # Dropdown for ROI Type Selection
        roi_types = list(self.all_rois.keys()) + list(self.all_rois["node_types"].keys())
        self.roi_type_menu = tk.StringVar(master)
        self.roi_type_menu.set("tile_scanning")
        self.dropdown = tk.OptionMenu(master, self.roi_type_menu, *roi_types, command=self.change_roi_type)
        self.dropdown.pack(side=tk.TOP, pady=10)

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.canvas.bind("<Button-3>", self.delete_roi)  # Right-click to delete ROI

        save_button = tk.Button(master, text="Save ROIs", command=self.save_rois)
        save_button.pack(side=tk.BOTTOM, pady=10)

    def load_existing_rois(self):
        """Load existing ROIs from the JSON file."""
        if os.path.exists(self.roi_file):
            with open(self.roi_file, "r") as f:
                self.all_rois = json.load(f)
        self.draw_rois()

    def draw_rois(self):
        """Draw existing ROIs on the canvas for the selected category."""
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

        if self.current_roi_type in self.all_rois:
            self.rectangles = self.all_rois[self.current_roi_type]
        else:
            self.rectangles = self.all_rois["node_types"].get(self.current_roi_type, [])

        self.rect_ids = []
        for roi in self.rectangles:
            rect_id = self.canvas.create_rectangle(*roi, outline="red", width=2)
            self.rect_ids.append(rect_id)

    def change_roi_type(self, value):
        """Change the currently selected ROI type."""
        self.current_roi_type = value
        self.draw_rois()

    def on_button_press(self, event):
        """Start drawing a new ROI."""
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="blue", width=2
        )

    def on_mouse_drag(self, event):
        """Update rectangle as mouse moves."""
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        """Save the new ROI to the selected category."""
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)
        self.rectangles.append((self.start_x, self.start_y, end_x, end_y))
        self.rect_ids.append(self.rect_id)
        print(f"✅ ROI added for {self.current_roi_type}: ({self.start_x}, {self.start_y}, {end_x}, {end_y})")

    def delete_roi(self, event):
        """Delete an ROI if right-clicked."""
        click_x = self.canvas.canvasx(event.x)
        click_y = self.canvas.canvasy(event.y)

        for i, roi in enumerate(self.rectangles):
            x1, y1, x2, y2 = roi
            if x1 <= click_x <= x2 and y1 <= click_y <= y2:
                print(f"❌ Deleting ROI for {self.current_roi_type}: {roi}")
                self.canvas.delete(self.rect_ids[i])
                del self.rectangles[i]
                del self.rect_ids[i]
                break

    def save_rois(self):
        """Save the updated ROIs to the JSON file."""
        if self.current_roi_type in self.all_rois:
            self.all_rois[self.current_roi_type] = self.rectangles
        else:
            self.all_rois["node_types"][self.current_roi_type] = self.rectangles

        with open(self.roi_file, "w") as f:
            json.dump(self.all_rois, f, indent=4)
        print("✅ ROIs saved to rois.json")
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ROISelector(root)
    root.mainloop()
