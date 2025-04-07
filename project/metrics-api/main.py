from flask import Flask, jsonify
from scheduler import generate_dynamic_config
import threading, time, os
from datetime import datetime

app = Flask(__name__)

CONFIG_PATH = "/traefik/dynamic_conf.yml"

def update_config():
    config = generate_dynamic_config()
    with open(CONFIG_PATH, "w") as f:
        f.write(config)
    print(f"[{datetime.now()}] [INFO] Config updated.")
    return config

# 주기적 실행 쓰레드
def schedule_loop():
    while True:
        update_config()
        time.sleep(5)       # 5초 주기로 업데이트

@app.route("/update")
def update_by_request():
    update_config()
    return jsonify({"status": "updated"})

# 주기적 쓰레드 실행 시작
if __name__ == '__main__':
    threading.Thread(target=schedule_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)
