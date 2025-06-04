import sqlite3

db_path = "map_data.db"

# Connect to SQLite and check the table structure
with sqlite3.connect(db_path) as conn:
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(digested_screenshots);")
    columns = cursor.fetchall()

# Display column details
print("Table Structure for 'digested_screenshots':")
for col in columns:
    print(col)
