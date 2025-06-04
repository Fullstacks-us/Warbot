import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import json
import os
import glob
import subprocess

class TileScannerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Tile Scanner - Live Screenshot & ROI Manager")

        # GUI with Tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tabs
        self.roi_tab = tk.Frame(self.notebook)
        self.ocr_tab = tk.Frame(self.notebook)
        self.screenshot_tab = tk.Frame(self.notebook)
        self.adb_tab = tk.Frame(self.notebook)
        self.settings_tab = tk.Frame(self.notebook)

        self.notebook.add(self.roi_tab, text="ROI Editor")
        self.notebook.add(self.ocr_tab, text="OCR Testing")
        self.notebook.add(self.screenshot_tab, text="Live Screenshots")
        self.notebook.add(self.adb_tab, text="ADB Tools")
        self.notebook.add(self.settings_tab, text="Settings")

        # Load JSON Data
        self.roi_file = "rois.json"
        self.load_existing_rois()

        # Setup GUI Tabs
        self.setup_roi_editor()
        self.setup_ocr_tab()
        self.setup_screenshot_tab()
        self.setup_adb_tab()
        self.setup_settings_tab()

    ### **🟢 ROI EDITOR TAB (FIXED)**
    def setup_roi_editor(self):
        """Sets up the ROI Editor tab."""
        self.canvas = tk.Canvas(self.roi_tab, cursor="cross", bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        tk.Button(self.roi_tab, text="📂 Load Image", command=self.load_image).pack(pady=5)
        tk.Button(self.roi_tab, text="💾 Save ROIs", command=self.save_rois).pack(pady=5)

        self.label_entry = tk.Entry(self.roi_tab)
        self.label_entry.pack(pady=5)
        self.label_entry.insert(0, "Enter ROI Label")

        self.rectangles = []
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.tk_image = None

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

    def load_image(self):
        """Loads an image into the ROI editor."""
        file_path = filedialog.askopenfilename(title="Select an Image", filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if not file_path:
            return

        self.image = Image.open(file_path)
        self.tk_image = ImageTk.PhotoImage(self.image)

        self.canvas.config(width=self.tk_image.width(), height=self.tk_image.height())
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

    def on_button_press(self, event):
        """Start drawing a new ROI."""
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="blue", width=2)

    def on_mouse_drag(self, event):
        """Update rectangle as mouse moves."""
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        """Save the new ROI with a label."""
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)
        label = self.label_entry.get().strip()

        if not label or label == "Enter ROI Label":
            label = "Unnamed"

        roi_data = {"label": label, "coords": (self.start_x, self.start_y, end_x, end_y)}
        self.rectangles.append(roi_data)
        print(f"✅ ROI added: {roi_data}")

    def save_rois(self):
        """Saves labeled ROIs to a file."""
        self.all_rois["regions"] = self.rectangles
        with open(self.roi_file, "w") as f:
            json.dump(self.all_rois, f, indent=4)
        print("✅ ROIs saved!")

    ### **🟢 SCREENSHOT HANDLING (FIXED)**
    def setup_screenshot_tab(self):
        """Sets up the live screenshot viewer."""
        tk.Label(self.screenshot_tab, text="Live Screenshot Viewer", font=("Arial", 14)).pack()

        self.screenshot_display = tk.Label(self.screenshot_tab, bg="gray", width=50, height=20)
        self.screenshot_display.pack()

        tk.Button(self.screenshot_tab, text="🔄 Refresh Screenshot", command=self.load_latest_screenshot).pack(pady=5)
        tk.Button(self.screenshot_tab, text="📂 Browse Screenshot", command=self.browse_screenshot).pack(pady=5)

        self.load_latest_screenshot()

    def load_latest_screenshot(self):
        """Loads the most recent screenshot from the 'screenshots' folder."""
        screenshot_dir = "screenshots"
        os.makedirs(screenshot_dir, exist_ok=True)

        files = sorted(glob.glob(os.path.join(screenshot_dir, "*.png")), key=os.path.getmtime, reverse=True)
        if files:
            self.display_screenshot(files[0])
        else:
            messagebox.showwarning("No Screenshots", "No screenshots found.")

    def browse_screenshot(self):
        """Manually browse and load a screenshot."""
        file_path = filedialog.askopenfilename(title="Select Screenshot", filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if file_path:
            self.display_screenshot(file_path)

    def display_screenshot(self, file_path):
        """Displays the selected screenshot."""
        img = Image.open(file_path)
        img.thumbnail((400, 400))
        self.tk_screenshot = ImageTk.PhotoImage(img)
        self.screenshot_display.config(image=self.tk_screenshot)
        self.screenshot_display.image = self.tk_screenshot

    ### **🟢 ADB TOOLS (FIXED)**
    def setup_adb_tab(self):
        """Sets up the ADB tab."""
        tk.Label(self.adb_tab, text="ADB Commands", font=("Arial", 14)).pack()

        tk.Button(self.adb_tab, text="🔌 Connect to Device", command=self.connect_to_device).pack(pady=5)
        tk.Button(self.adb_tab, text="📸 Capture Screenshot", command=self.capture_adb_screenshot).pack(pady=5)

    def connect_to_device(self):
        """Connects to an Android device via ADB."""
        messagebox.showinfo("ADB", "Connecting to device... (Functionality not implemented yet)")

    def capture_adb_screenshot(self):
        """Captures a screenshot using ADB and saves it."""
        adb_command = "adb shell screencap -p /sdcard/screenshot.png && adb pull /sdcard/screenshot.png screenshots/screenshot.png"
        try:
            subprocess.run(adb_command, shell=True, check=True)
            self.load_latest_screenshot()
            messagebox.showinfo("ADB", "Screenshot captured and loaded!")
        except subprocess.CalledProcessError:
            messagebox.showerror("ADB Error", "Failed to capture screenshot. Ensure ADB is installed and device is connected.")

if __name__ == "__main__":
    root = tk.Tk()
    app = TileScannerGUI(root)
    root.mainloop()
