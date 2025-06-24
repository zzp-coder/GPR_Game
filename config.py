import os
from dotenv import load_dotenv

load_dotenv()  # 只在本地生效，云端不影响

DB_PATH = os.getenv('DB_PATH', 'db/game.db')