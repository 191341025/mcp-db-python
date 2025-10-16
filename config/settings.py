# 读取 .env / toml 配置
from dotenv import load_dotenv
import os

load_dotenv()

DB_CONFIG = {
    "type": os.getenv("DB_TYPE", "mysql"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", ""),
    "database": os.getenv("DB_NAME", "")
}
