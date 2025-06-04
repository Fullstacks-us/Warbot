import threading
import tkinter as tk
from tkinter import messagebox
from tile_scanner import TileScanner
import json
import time


class TileScannerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Tile Scanner - Live Debugging")

        # Initialize scanner
        self.scanner = TileScanner()
        self.scan_thread = None

        # Thread control flags
        self.scanning_event = threading.Event()  # ✅ Controls pause/resume
        self.stop_requested = False  

        # UI Layout
        self.start_button = tk.Button(root, text="Start Scan", command=self.start_scan, width=15, height=2, bg="green")
        self.start_button.pack(pady=5)

        self.pause_button = tk.Button(root, text="Pause Scan", command=self.pause_scan, width=15, height=2, bg="orange")
        self.pause_button.pack(pady=5)

        self.stop_button = tk.Button(root, text="Stop Scan", command=self.stop_scan, width=15, height=2, bg="red")
        self.stop_button.pack(pady=5)

        self.log_label = tk.Label(root, text="Scanned Tiles:")
        self.log_label.pack()

        self.log_listbox = tk.Listbox(root, width=80, height=10)
        self.log_listbox.pack()

    def start_scan(self):
        """Starts scanning tiles in a separate thread."""
        if self.scan_thread and self.scan_thread.is_alive():
            self.log_message("⚠️ Scan is already running!")
            return

        self.scanning_event.set()  # ✅ Allow scanning
        self.stop_requested = False  
        self.scan_thread = threading.Thread(target=self.run_scan, daemon=True)
        self.scan_thread.start()
        self.log_message("🔍 Scanning started...")

    def pause_scan(self):
        """Pauses or resumes scanning."""
        if self.scanning_event.is_set():
            self.scanning_event.clear()  # ✅ Pause scanning
            self.log_message("⏸️ Scan paused.")
        else:
            self.scanning_event.set()  # ✅ Resume scanning
            self.log_message("▶️ Resumed scan.")

    def stop_scan(self):
        """Stops scanning completely."""
        self.stop_requested = True  # ✅ Stop the scan loop
        self.scanning_event.set()  # ✅ Ensure it’s not paused (so it can exit)
        self.log_message("🛑 Stopping scan... Please wait.")

    def run_scan(self):
        """Runs the tile scanning process while checking stop/pause conditions."""
        kingdom = 914  # Example kingdom
        x_start, x_end = 7, 511 # Example coordinates
        y_start, y_end = 7, 1023
        move_step = 7  # Example step size

        for x in range(x_start, x_end + 1, move_step):
            for y in range(y_start, y_end + 1, move_step):
                if self.stop_requested:  # ✅ Check stop flag
                    self.log_message("🛑 Scan stopped successfully.")
                    return  # Exit the function properly

                self.scanning_event.wait(0.1)  # ✅ Pause handling (waits until resumed)

                self.log_message(f"🌍 Navigating to {kingdom}:{x},{y}...")
                
                # 🔹 Add stop check inside `scan_location`
                if not self.scanner.scan_location(kingdom, x, y, stop_flag=self.stop_requested):
                    self.log_message("🛑 Scan interrupted mid-scan.")
                    return

                # Update log with last 10 tiles scanned
                try:
                    with open("tile_scan_results.json", "r") as f:
                        tiles = json.load(f)
                        self.log_listbox.delete(0, tk.END)  # Clear previous logs
                        for tile in tiles[-10:]:  # Show last 10 scanned tiles
                            log_text = f"{tile['kingdom']}:{tile['x']},{tile['y']} - {tile['tile_type']}"
                            self.log_listbox.insert(tk.END, log_text)
                except FileNotFoundError:
                    self.log_message("⚠️ No scan results found yet.")

    def log_message(self, message):
        """Logs messages to the UI without freezing."""
        self.log_listbox.insert(tk.END, message)
        self.log_listbox.yview(tk.END)  # Auto-scroll
        self.root.update_idletasks()

if __name__ == "__main__":
    root = tk.Tk()
    app = TileScannerGUI(root)
    root.mainloop()
