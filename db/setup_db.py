from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).parent / "db/topics.db"  # adjust to your project root

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# run schema.sql
with open(Path(__file__).parent / "db/schema.sql", "r") as f:
    cursor.executescript(f.read())

conn.commit()
conn.close()
print("DB initialized")