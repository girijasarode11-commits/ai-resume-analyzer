import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect("resume.db")
    cursor = conn.cursor()

    # Analyses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            ats REAL,
            similarity REAL,
            final_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            email TEXT UNIQUE,
            password TEXT,
            reset_token TEXT,
            reset_expiry TEXT
        )
    """)

    conn.commit()
    conn.close()


# ---------------- ANALYSIS FUNCTIONS ----------------

def save_analysis(filename, ats, similarity, final_score):
    conn = sqlite3.connect("resume.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO analyses (filename, ats, similarity, final_score, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        filename,
        ats,
        similarity,
        final_score,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()


def get_all_analyses():
    conn = sqlite3.connect("resume.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, filename, ats, similarity, final_score, created_at
        FROM analyses
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows

def get_total_analyses():
    conn = sqlite3.connect("resume.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM analyses")
    total = cursor.fetchone()[0]

    conn.close()
    return total


def get_avg_scores():
    conn = sqlite3.connect("resume.db")
    cursor = conn.cursor()

    cursor.execute("SELECT AVG(ats), AVG(similarity) FROM analyses")
    row = cursor.fetchone()

    avg_ats = row[0] if row[0] is not None else 0
    avg_similarity = row[1] if row[1] is not None else 0

    conn.close()
    return round(avg_ats, 2), round(avg_similarity, 2)


def get_max_ats():
    conn = sqlite3.connect("resume.db")
    cursor = conn.cursor()

    cursor.execute("SELECT MAX(ats) FROM analyses")
    row = cursor.fetchone()

    max_ats = row[0] if row[0] is not None else 0

    conn.close()
    return max_ats

def get_ranked_resumes():
    conn = sqlite3.connect("resume.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM analyses
        ORDER BY final_score DESC
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows

# ---------------- USER AUTH FUNCTIONS ----------------

def create_user(username, email, password):
    conn = sqlite3.connect("resume.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
        (username, email, password)
    )

    conn.commit()
    conn.close()


def get_user(email):
    conn = sqlite3.connect("resume.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE email = ?",
        (email,)
    )

    user = cursor.fetchone()

    conn.close()
    return user


def get_total_users():
    conn = sqlite3.connect("resume.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]

    conn.close()
    return total


def delete_analysis(record_id):
    conn = sqlite3.connect("resume.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM analyses WHERE id=?", (record_id,))

    conn.commit()
    conn.close()


def get_user_analysis_count():
    conn = sqlite3.connect("resume.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM analyses")
    total = cursor.fetchone()[0]

    conn.close()
    return total


def get_best_ats():
    conn = sqlite3.connect("resume.db")
    cursor = conn.cursor()

    cursor.execute("SELECT MAX(ats) FROM analyses")
    best = cursor.fetchone()[0]

    conn.close()
    return best if best else 0



def get_ats_distribution():
    conn = sqlite3.connect("resume.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            SUM(CASE WHEN ats <= 40 THEN 1 ELSE 0 END),
            SUM(CASE WHEN ats > 40 AND ats <= 70 THEN 1 ELSE 0 END),
            SUM(CASE WHEN ats > 70 THEN 1 ELSE 0 END)
        FROM analyses
    """)

    row = cursor.fetchone()
    conn.close()

    return list(row)

def get_upload_trend():
    conn = sqlite3.connect("resume.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DATE(created_at), COUNT(*)
        FROM analyses
        GROUP BY DATE(created_at)
        ORDER BY DATE(created_at)
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows

def init_cache_table():
    conn = sqlite3.connect("resume.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_hash TEXT UNIQUE,
            feedback TEXT
        )
    """)

    conn.commit()
    conn.close()

def get_recent_analyses(limit=2):
    conn = sqlite3.connect("resume.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, filename, ats, similarity, final_score, created_at
        FROM analyses
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()
    return rows