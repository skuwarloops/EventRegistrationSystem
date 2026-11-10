import sqlite3

DB_NAME = "events.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_connection()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS Events (
        evCode INTEGER PRIMARY KEY AUTOINCREMENT,
        evName TEXT NOT NULL,
        evDate DATE NOT NULL,
        evVenue TEXT NOT NULL,
        evRFee DECIMAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS Participants (
        partID INTEGER PRIMARY KEY AUTOINCREMENT,
        evCode INTEGER,
        partFName TEXT NOT NULL,
        partLName TEXT NOT NULL,
        partDRate DECIMAL NOT NULL DEFAULT 0,
        FOREIGN KEY (evCode) REFERENCES Events(evCode)
    );

    CREATE TABLE IF NOT EXISTS Registration (
        regCode INTEGER PRIMARY KEY AUTOINCREMENT,
        partID INTEGER NOT NULL,
        regDate DATE NOT NULL,
        regFPaid DECIMAL NOT NULL,
        regPMode TEXT NOT NULL,
        FOREIGN KEY (partID) REFERENCES Participants(partID)
    );
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database created!")