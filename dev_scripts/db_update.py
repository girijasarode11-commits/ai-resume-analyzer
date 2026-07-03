import sqlite3

conn = sqlite3.connect("resume.db")
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE users ADD COLUMN reset_token TEXT")
    print("Column added successfully!")
except sqlite3.OperationalError:
    print("Column already exists!")

conn.commit()
conn.close()