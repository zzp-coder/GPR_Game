import sqlite3
import os
from werkzeug.security import generate_password_hash

# 确保 /data 目录存在（Render 挂载点）
os.makedirs("/data", exist_ok=True)

conn = sqlite3.connect('/data/game.db')
c = conn.cursor()

# 重建表
c.execute('DROP TABLE IF EXISTS users')
c.execute('DROP TABLE IF EXISTS matches')

c.execute('''CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT,
    total_score REAL DEFAULT 0
)''')

c.execute('''CREATE TABLE matches (
    id INTEGER PRIMARY KEY,
    paragraph_id INTEGER,
    player1 TEXT,
    player2 TEXT,
    is_match BOOLEAN,
    selections_p1 TEXT,
    selections_p2 TEXT,
    score_p1 REAL,
    score_p2 REAL,
    duration_p1 REAL,
    duration_p2 REAL,
    attempts_json TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)''')

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
print("✅ Database initialized at /data/game.db")