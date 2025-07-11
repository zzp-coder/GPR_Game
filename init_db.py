import sqlite3
from werkzeug.security import generate_password_hash
import os
import json
from config import DB_PATH
print("🛠 Running init_db.py to initialize database...")
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

# 从环境变量读取 JSON 格式的用户名密码字典
users_json = os.getenv('USER_CREDENTIALS_JSON', '{}')
admin_pass = os.getenv('ADMIN_PASSWORD', 'admin')

try:
    user_dict = json.loads(users_json)
except json.JSONDecodeError:
    print("⚠️ USER_CREDENTIALS_JSON 格式错误，将不会添加用户")
    user_dict = {}

# 插入普通用户
for username, password in user_dict.items():
    # ✅ 排除 dave 和 carol，避免重复插入
    if username in ['dave', 'carol']:
        continue
    c.execute('INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)',
              (username, generate_password_hash(password), 'player'))

# ✅ 插入 dave 和 carol，保留原始积分
c.execute('INSERT OR REPLACE INTO users (username, password, role, total_score) VALUES (?, ?, ?, ?)',
          ('dave', generate_password_hash('changeme'), 'player', 907.05006))
c.execute('INSERT OR REPLACE INTO users (username, password, role, total_score) VALUES (?, ?, ?, ?)',
          ('carol', generate_password_hash('changeme'), 'player', 867.94994))
# 插入管理员
c.execute('INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)',
          ("admin", generate_password_hash(admin_pass), 'admin'))

conn.commit()
conn.close()
print("✅ Database initialized at", DB_PATH)