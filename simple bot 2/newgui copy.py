import tkinter as tk
from tkinter.filedialog import askopenfilename
from tkinter import messagebox
from PIL import Image, ImageTk
from adb_module import ADBModule
# ✅ Import NavigationTool properly
from navigation_tool import NavigationTool  

class ROIEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("ROI Editor")

        self.adb_module = ADBModule()  # ✅ Fix: Instantiate properly
        self.navigation_tool = NavigationTool()
        # Canvas setup
        self.canvas = tk.Canvas(root, width=800, height=600, bg="gray")
        self.canvas.pack(expand=True)

        # Buttons
        self.button_load = tk.Button(root, text="Load Image", command=self.load_image)
        self.button_load.pack()

        self.button_capture = tk.Button(root, text="Capture Screenshot", command=self.capture_screenshot)
        self.button_capture.pack()

        self.button_navigate = tk.Button(root, text="Navigate", command=self.navigate)
        self.button_navigate.pack()

        # ROI storage
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.image_ref = None  # ✅ Fix: Keep reference to prevent garbage collection
        self.rectangles = []

        # Bind mouse events for ROI selection
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

    def load_image(self):
        """Loads an image into the canvas."""
        file_path = askopenfilename(title="Select an Image", filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if not file_path:
            return

        try:
            image = Image.open(file_path)
            self.image_ref = ImageTk.PhotoImage(image)

            self.canvas.config(width=self.image_ref.width(), height=self.image_ref.height())
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image_ref)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")

    def capture_screenshot(self):
        """Captures a screenshot using NavigationTool."""
        try:
            self.adb_module.capture_screenshot("/path/to/local/file.png")  # Ensure correct path
            messagebox.showinfo("Success", "Screenshot captured!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to capture screenshot: {e}")

    def navigate(self):
        """Handles navigation logic (implement as needed)."""
        print("Navigation triggered.")

    def on_button_press(self, event):
        """Start drawing a new ROI."""
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="red", width=2)

    def on_mouse_drag(self, event):
        """Update rectangle as mouse moves."""
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        """Save the new ROI."""
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)
        self.rectangles.append((self.start_x, self.start_y, end_x, end_y))
        print(f"✅ ROI added: ({self.start_x}, {self.start_y}, {end_x}, {end_y})")

if __name__ == "__main__":
    root = tk.Tk()
    app = ROIEditor(root)
    root.mainloop()
