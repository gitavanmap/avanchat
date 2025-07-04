import psycopg2
from dotenv import load_dotenv
import os

load_dotenv('../.env')

configs = [
    {"host": "127.0.0.1", "user": "postgres"},
    {"host": "127.0.0.1", "user": "user"},
    {"host": "localhost", "user": "postgres"},
    {"host": "localhost", "user": "user"},
]

for config in configs:
    try:
        conn = psycopg2.connect(
            host=config["host"],
            database="fiscal_chat_db",
            user=config["user"],
            password="password",
            port="5432"
        )
        print(f"✅ Conexiune OK cu {config['user']}@{config['host']}!")
        conn.close()
        break
    except Exception as e:
        print(f"❌ {config['user']}@{config['host']}: {e}")
