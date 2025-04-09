from flask import Flask
from scheduler import generate_dynamic_config
import threading, time, os
from datetime import datetime

app = Flask(__name__)

CONFIG_PATH = "/etc/traefik/dynamic_conf.yml"

# metric-api 업데이트 로그 생성
def update_config():
    config = generate_dynamic_config()
    with open(CONFIG_PATH, "w") as f:
        f.write(config)
    print(f"[{datetime.now()}] [INFO] Config updated.")
    return config

# 주기적으로 (5초) scheduler.py 실행
def schedule_loop():
    while True:
        update_config()
        time.sleep(5)

# 실행 시작
if __name__ == '__main__':
    threading.Thread(target=schedule_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)
