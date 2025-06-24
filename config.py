# === config.py ===
import os
import json
from dotenv import load_dotenv
load_dotenv()

DB_PATH = os.getenv('DB_PATH', 'db/game.db')

def load_credentials():
    # 优先从环境变量读取
    env_json = os.getenv("USER_CREDENTIALS_JSON")
    admin_pass = os.getenv("ADMIN_PASSWORD", "admin")

    if env_json:
        try:
            users = json.loads(env_json)
            return users, admin_pass
        except Exception as e:
            print("⚠️ Failed to parse USER_CREDENTIALS_JSON:", e)
            return {}, admin_pass

    # 如果本地运行就读取 YAML 文件
    try:
        import yaml
        with open("local_credentials.yaml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("users", {}), data.get("admin_password", "admin")
    except Exception as e:
        print("⚠️ Failed to load local_credentials.yaml:", e)
        return {}, admin_pass

USER_CREDENTIALS, ADMIN_PASSWORD = load_credentials()