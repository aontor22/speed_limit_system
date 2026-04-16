import sqlite3
from datetime import datetime

DB_PATH = "database.db"

def init_db():
    """
    Initializes the SQLite database and creates the violations table if it doesn't exist.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS violations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            detected_speed INTEGER,
            speed_limit INTEGER,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

def insert_violation(detected_speed, speed_limit, status):
    """
    Inserts a new record into the violations table.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute('''
            INSERT INTO violations (timestamp, detected_speed, speed_limit, status)
            VALUES (?, ?, ?, ?)
        ''', (timestamp, detected_speed, speed_limit, status))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Database Insert Error: {e}")
        return False

def get_recent_violations(limit=10):
    """
    Retrieves the last N violations from the database.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        # This allows us to access columns by name like a dictionary
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM violations ORDER BY id DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        
        # Convert sqlite3.Row objects to list of dictionaries for JSON response
        results = [dict(row) for row in rows]
        
        conn.close()
        return results
    except Exception as e:
        print(f"Database Fetch Error: {e}")
        return []