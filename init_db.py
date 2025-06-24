import sqlite3
from werkzeug.security import generate_password_hash
import os
from config import DB_PATH

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute('DROP TABLE IF EXISTS users')
c.execute('DROP TABLE IF EXISTS matches')
c.execute('DROP TABLE IF EXISTS progress')

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

c.execute('''CREATE TABLE IF NOT EXISTS progress (
    room TEXT PRIMARY KEY,
    paragraph_index INTEGER
)''')

# 从环境变量读初始密码，没有则用默认值
import os

def getenv_or_default(key, default):
    return os.environ.get(key, default)

users = [
    ('alice', getenv_or_default('ALICE_PASS', '1234'), 'player'),
    ('bob', getenv_or_default('BOB_PASS', '1234'), 'player'),
    ('carol', getenv_or_default('CAROL_PASS', '1234'), 'player'),
    ('dave', getenv_or_default('DAVE_PASS', '1234'), 'player'),
    ('admin', getenv_or_default('ADMIN_PASS', 'admin'), 'admin')
]

for u, p, r in users:
    c.execute('INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)',
              (u, generate_password_hash(p), r))

conn.commit()
conn.close()
print("✅ Database initialized at", DB_PATH)