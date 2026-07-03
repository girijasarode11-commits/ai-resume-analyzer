import sqlite3

conn = sqlite3.connect("resume.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM analyses")
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()