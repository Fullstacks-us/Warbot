import os
import json
from tkinter import Tk, Canvas, Label, Button, OptionMenu, StringVar, Entry
from PIL import Image, ImageTk
from adb_module2 import ADBModule  # Assuming the ADBModule is in the same project folder


class TemplateModule:
    def __init__(self, template_dir="templates"):
        print("Initializing TemplateModule...")  # Debugging initialization
        self.template_dir = template_dir
        self.adb = ADBModule()  # Initialize ADBModule instance
        os.makedirs(self.template_dir, exist_ok=True)
        self.template_metadata_file = os.path.join(self.template_dir, "metadata.json")
        self._load_metadata()

        print(f"TemplateModule initialized. Template directory: {self.template_dir}")
        print(f"Metadata file path: {self.template_metadata_file}")

    def _load_metadata(self):
        """Load metadata for templates."""
        print("Loading metadata...")  # Debugging metadata loading
        if os.path.exists(self.template_metadata_file):
            with open(self.template_metadata_file, "r") as f:
                self.template_metadata = json.load(f)
            print("Metadata loaded successfully.")
        else:
            self.template_metadata = {}
            print("No metadata file found. Starting with an empty metadata dictionary.")

    def _save_metadata(self):
        """Save metadata for templates."""
        print("Saving metadata...")  # Debugging metadata saving
        with open(self.template_metadata_file, "w") as f:
            json.dump(self.template_metadata, f, indent=4)
        print("Metadata saved successfully.")

    def gui_select_roi(self, image_path):
        """
        Enhanced GUI for selecting ROI and entering template details.

        Args:
            image_path (str): Path to the image file.

        Returns:
            tuple: Selected ROI as (x, y, width, height) and template details.
        """
        print(f"Opening image for ROI selection: {image_path}")  # Debugging image opening

        roi = []
        template_details = {"category": None, "level": None, "label": None}
        start_x, start_y = [0, 0]
        rect_id = None

        def on_mouse_press(event):
            nonlocal start_x, start_y, rect_id
            start_x, start_y = event.x, event.y
            if rect_id:
                canvas.delete(rect_id)
            rect_id = canvas.create_rectangle(start_x, start_y, start_x, start_y, outline="red", width=2)
            print(f"Mouse pressed at: ({start_x}, {start_y})")  # Debugging mouse press

        def on_mouse_drag(event):
            nonlocal rect_id
            canvas.coords(rect_id, start_x, start_y, event.x, event.y)
            print(f"Mouse dragging: ({start_x}, {start_y}) to ({event.x}, {event.y})")

        def on_mouse_release(event):
            nonlocal roi
            end_x, end_y = event.x, event.y
            print(f"Mouse released at: ({end_x}, {end_y})")  # Debugging mouse release

            # Calculate ROI
            x_min = max(0, min(start_x, end_x))
            y_min = max(0, min(start_y, end_y))
            x_max = min(img_width, max(start_x, end_x))
            y_max = min(img_height, max(start_y, end_y))

            # Validate ROI
            width = x_max - x_min
            height = y_max - y_min
            if width > 0 and height > 0:
                roi = (x_min, y_min, width, height)
                roi_label.config(text=f"ROI Selected: {roi}")
                print(f"ROI selected: {roi}")  # Debugging ROI selection

        def update_levels(*args):
            """Update levels based on the selected category."""
            category = category_var.get()
            print(f"Category changed to: {category}")  # Debugging category change

            # Reset the level dropdown
            level_menu["menu"].delete(0, "end")
            label_entry.config(state="normal" if category == "UI Button" else "disabled")

            if category == "Darknests":
                # Levels 1-6 for Darknests
                for level in range(1, 7):
                    level_menu["menu"].add_command(label=str(level), command=lambda value=level: level_var.set(value))
                level_var.set("1")  # Set default level to 1
            elif category in ["Food", "Stone", "Ore", "Wood", "Gold"]:
                # Levels 1-5 for resource categories
                for level in range(1, 6):
                    level_menu["menu"].add_command(label=str(level), command=lambda value=level: level_var.set(value))
                level_var.set("1")  # Set default level to 1
            elif category == "Castles":
                # Levels 1-25 for Castles
                for level in range(1, 26):
                    level_menu["menu"].add_command(label=str(level), command=lambda value=level: level_var.set(value))
                level_var.set("1")  # Set default level to 1
            elif category == "UI Button":
                level_var.set("N/A")  # No levels for UI Button

        def save_template_details():
            """Save template details and close GUI."""
            template_details["category"] = category_var.get().strip()
            template_details["level"] = level_var.get().strip()
            template_details["label"] = label_entry.get().strip() if category_var.get() == "UI Button" else None

            print(f"Template details: {template_details}")  # Debugging template details

            if not roi:
                status_label.config(text="Error: ROI not selected.", fg="red")
                print("Error: ROI not selected.")  # Debugging error
            else:
                self.template_metadata[template_details["category"]] = self.template_metadata.get(
                    template_details["category"], {}
                )
                self.template_metadata[template_details["category"]][template_details["level"]] = {
                    "roi": roi,
                    "label": template_details["label"]
                }
                self._save_metadata()

                # Save the cropped ROI as a new image
                roi_path = os.path.join(
                    self.template_dir,
                    f"{template_details['category']}_{template_details['level']}.png"
                )
                original_image = Image.open(image_path)
                cropped_image = original_image.crop((roi[0], roi[1], roi[0] + roi[2], roi[1] + roi[3]))
                cropped_image.save(roi_path)
                print(f"Cropped ROI saved as: {roi_path}")

                status_label.config(text="Template saved successfully!", fg="green")
                print("Template saved successfully!")  # Debugging success
                root.destroy()

        # Load image
        image = Image.open(image_path)
        img_width, img_height = image.size
        print(f"Image dimensions: {img_width}x{img_height}")  # Debugging image dimensions

        # Create Tkinter GUI
        root = Tk()
        root.title("Create Template")
        print("Tkinter GUI initialized.")  # Debugging GUI initialization

        # Add image canvas
        canvas = Canvas(root, width=img_width, height=img_height, bg="gray")
        canvas.grid(row=0, column=0, columnspan=2)

        img_tk = ImageTk.PhotoImage(image)
        canvas.create_image(0, 0, anchor="nw", image=img_tk)

        # Bind mouse events
        canvas.bind("<ButtonPress-1>", on_mouse_press)
        canvas.bind("<B1-Motion>", on_mouse_drag)
        canvas.bind("<ButtonRelease-1>", on_mouse_release)

        # Category dropdown
        Label(root, text="Category:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        categories = ["Darknests", "Food", "Stone", "Ore", "Wood", "Gold", "Castles", "UI Button"]
        category_var = StringVar(root)
        category_var.set(categories[0])
        category_menu = OptionMenu(root, category_var, *categories, command=update_levels)
        category_menu.grid(row=1, column=1, padx=5, pady=5)

        # Level dropdown
        Label(root, text="Level:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        level_var = StringVar(root)
        level_var.set("1")
        level_menu = OptionMenu(root, level_var, "1")
        level_menu.grid(row=2, column=1, padx=5, pady=5)

        # Label for UI Button
        Label(root, text="Label:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        label_entry = Entry(root, width=20)
        label_entry.grid(row=3, column=1, padx=5, pady=5)
        label_entry.config(state="disabled")

        # ROI status and save button
        roi_label = Label(root, text="ROI Not Selected", fg="blue")
        roi_label.grid(row=4, column=0, columnspan=2)
        save_button = Button(root, text="Save Template", command=save_template_details)
        save_button.grid(row=5, column=0, columnspan=2, pady=10)

        # Status label
        status_label = Label(root, text="")
        status_label.grid(row=6, column=0, columnspan=2)

        # Start GUI loop
        print("Starting Tkinter main loop...")  # Debugging event loop
        root.mainloop()
        print("Tkinter main loop ended.")  # Debugging event loop end

        if not roi or not all(template_details.values()):
            raise ValueError("Template creation aborted or incomplete.")
        return roi, template_details


# Example usage
if __name__ == "__main__":
    template_module = TemplateModule()

    # Example image path (replace with an actual image path)
    image_path = "screenshots/emulator-5554_screenshot.png"

    try:
        roi, details = template_module.gui_select_roi(image_path)
        print(f"Selected ROI: {roi}, Details: {details}")
    except Exception as e:
        print(f"Error: {e}")
