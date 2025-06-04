import sqlite3
import pandas as pd
import os
import tkinter as tk
from tkinter import ttk, messagebox

DB_PATH = "map_data.db"

class DatabaseViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Map Data Viewer")
        self.root.geometry("900x500")

        # Search Bar
        self.search_var = tk.StringVar()
        search_frame = tk.Frame(self.root)
        search_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(search_frame, text="Search", command=self.filter_data).pack(side=tk.LEFT, padx=5)
        tk.Button(search_frame, text="Reset", command=self.load_data).pack(side=tk.LEFT, padx=5)
        tk.Button(search_frame, text="Refresh", command=self.load_data).pack(side=tk.RIGHT, padx=5)

        # Clear Database Button
        tk.Button(search_frame, text="Clear Records", command=self.clear_records, bg="red", fg="white").pack(side=tk.RIGHT, padx=5)

        # Table (Treeview)
        self.tree = ttk.Treeview(self.root, columns=("ID", "ADB X", "ADB Y", "X", "Y", "Type", "Details", "Kingdom X", "Kingdom Y", "Processed At"), show="headings")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Column Headings
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.CENTER, width=100)

        # Load Database
        self.load_data()

    def load_data(self):
        """Load all data from the database and display it in the table."""
        if not os.path.exists(DB_PATH):
            messagebox.showerror("Error", "Database file not found. Run the scanner first!")
            return

        try:
            with sqlite3.connect(DB_PATH) as conn:
                df = pd.read_sql_query("SELECT * FROM tiles ORDER BY processed_at DESC", conn)

            # Clear the table
            for row in self.tree.get_children():
                self.tree.delete(row)

            # Insert data into table
            for _, row in df.iterrows():
                self.tree.insert("", tk.END, values=tuple(row))

        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load data: {e}")

    def filter_data(self):
        """Filter the displayed data based on the search query."""
        search_term = self.search_var.get().lower()
        if not search_term:
            self.load_data()
            return

        try:
            with sqlite3.connect(DB_PATH) as conn:
                query = f"""
                    SELECT * FROM tiles 
                    WHERE LOWER(node_type) LIKE '%{search_term}%'
                    OR LOWER(details) LIKE '%{search_term}%'
                    OR CAST(x AS TEXT) LIKE '%{search_term}%'
                    OR CAST(y AS TEXT) LIKE '%{search_term}%'
                    OR CAST(kingdom_x AS TEXT) LIKE '%{search_term}%'
                    OR CAST(kingdom_y AS TEXT) LIKE '%{search_term}%'
                    ORDER BY processed_at DESC
                """
                df = pd.read_sql_query(query, conn)

            # Clear the table
            for row in self.tree.get_children():
                self.tree.delete(row)

            # Insert filtered data into table
            for _, row in df.iterrows():
                self.tree.insert("", tk.END, values=tuple(row))

        except Exception as e:
            messagebox.showerror("Search Error", f"Failed to filter data: {e}")

    def clear_records(self):
        """Deletes all records from the database after confirmation."""
        confirm = messagebox.askyesno("Clear Database", "⚠ Are you sure you want to delete ALL records? This action cannot be undone.")
        if confirm:
            try:
                with sqlite3.connect(DB_PATH) as conn:
                    conn.execute("DELETE FROM tiles")
                    conn.commit()

                self.load_data()  # Refresh table
                messagebox.showinfo("Success", "✅ All records have been deleted successfully.")

            except Exception as e:
                messagebox.showerror("Error", f"❌ Failed to clear database: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DatabaseViewer(root)
    root.mainloop()
