
import sqlite3

conn = sqlite3.connect("resume.db")
cursor = conn.cursor()

try:
    cursor.execute(
        "ALTER TABLE analyses ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    )
    print("Timestamp column added successfully.")
except Exception as e:
    print("Maybe already exists:", e)

conn.commit()
conn.close()

