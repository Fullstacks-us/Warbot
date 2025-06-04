import sqlite3

db_path = "map_data.db"

with sqlite3.connect(db_path) as conn:
    cursor = conn.cursor()

    # Add tile_type column if it does not exist
    cursor.execute("PRAGMA table_info(digested_screenshots);")
    existing_columns = [row[1] for row in cursor.fetchall()]

    if "tile_type" not in existing_columns:
        print("Adding 'tile_type' column to database...")
        cursor.execute("ALTER TABLE digested_screenshots ADD COLUMN tile_type TEXT DEFAULT 'unknown';")
        conn.commit()
        print("✅ Column 'tile_type' added successfully!")
    else:
        print("✅ Column 'tile_type' already exists!")
