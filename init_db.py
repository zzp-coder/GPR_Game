# init_db.py
import sqlite3
from werkzeug.security import generate_password_hash
import os

DB_PATH = "/data/game.db"
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# 清空旧表（可选）
c.execute('DROP TABLE IF EXISTS users')
c.execute('DROP TABLE IF EXISTS matches')
c.execute('DROP TABLE IF EXISTS progress')

# 用户表
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT,
    total_score REAL DEFAULT 0
)''')

# 匹配记录表
c.execute('''CREATE TABLE IF NOT EXISTS matches (
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

# 新增：记录每个房间的段落进度
c.execute('''CREATE TABLE IF NOT EXISTS progress (
    room TEXT PRIMARY KEY,
    paragraph_index INTEGER
)''')

# 初始用户
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
print("✅ Database initialized at", DB_PATH)