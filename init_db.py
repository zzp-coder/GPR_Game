import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('db/game.db')
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT,
    total_score REAL DEFAULT 0
)''')

c.execute('''CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY,
    paragraph_id INTEGER,
    player1 TEXT,
    player2 TEXT,
    selections_p1 TEXT,
    selections_p2 TEXT,
    is_match BOOLEAN,
    score_p1 REAL,
    score_p2 REAL,
    duration_p1 REAL,
    duration_p2 REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)''')

# 添加初始用户
users = [
    ('alice', '1234', 'player'),
    ('bob', '1234', 'player'),
    ('carol', '1234', 'player'),
    ('dave', '1234', 'player'),
    ('admin', 'admin', 'admin')
]

for u, p, r in users:
    c.execute('INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)',
              (u, generate_password_hash(p), r))

conn.commit()
conn.close()
print("Database initialized.")