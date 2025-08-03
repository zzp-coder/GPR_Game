import sqlite3
from werkzeug.security import generate_password_hash
import os
import json
from config import DB_PATH

print("🛠 Running init_db.py to initialize database...")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# 删除旧表
c.execute('DROP TABLE IF EXISTS users')
c.execute('DROP TABLE IF EXISTS matches')
c.execute('DROP TABLE IF EXISTS progress')

# 创建新表
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

# 读取用户信息
users_json = os.getenv('USER_CREDENTIALS_JSON', '{}')
admin_pass = os.getenv('ADMIN_PASSWORD', 'admin')

try:
    user_dict = json.loads(users_json)
except json.JSONDecodeError:
    print("⚠️ USER_CREDENTIALS_JSON 格式错误，将不会添加用户")
    user_dict = {}

# 插入普通用户
for username, password in user_dict.items():
    c.execute('INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)',
              (username, generate_password_hash(password), 'player'))

# 插入管理员
c.execute('INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)',
          ("admin", generate_password_hash(admin_pass), 'admin'))

# ✅ 额外更新
bonus_scores = {
    "dave": 17593.38835,
    "carol": 17062.61165,
    "bob": 14623.74834,
    "alice": 14939.25172
}
for user, score in bonus_scores.items():
    c.execute('UPDATE users SET total_score = ? WHERE username = ?', (score, user))

conn.commit()
conn.close()
print("✅ Database initialized at", DB_PATH)