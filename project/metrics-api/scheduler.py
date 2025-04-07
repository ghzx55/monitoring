import requests
from datetime import datetime
import time

PROMETHEUS_URL = "http://211.183.3.200:9090"
QUERY = '100 - avg by(instance)(rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100'

# Traefik 설정 경로
CONFIG_PATH = "/traefik/dynamic_conf.yml"

def get_node_cpu_usage(retries=3, delay=3):   # prometheus 불러오기 실패시 최대 3번까지 다시 시도
    for attempt in range(retries):
        try:
            res = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": QUERY})
            res.raise_for_status()
            result = res.json()["data"]["result"]

            usage = []
            for item in result:
                instance = item["metric"]["instance"]
                value = float(item["value"][1])  # CPU 사용률 (%)
                usage.append((instance, value))
            return usage

        except Exception as e:
            print(f"[ERROR] Prometheus 쿼리 실패 (시도 {attempt + 1}): {e}")
            time.sleep(delay)

    return []

def get_best_node():
    usage = get_node_cpu_usage()
    if not usage:
        print("[ERROR] Prometheus에서 서버 정보 못 가져옴")
        return None

    # 가장 CPU 사용률 낮은 노드 선택
    best_node = min(usage, key=lambda x: x[1])
    print(f"[INFO] Best node: {best_node[0]} (CPU: {best_node[1]:.2f}%)")
    return best_node[0]

def generate_dynamic_config():
    best_node = get_best_node()
    if not best_node:
        return f"""\
http:
  routers:
    dynamic-router:
      rule: "PathPrefix(`/`)"
      service: dynamic-service
      entryPoints:
        - web

    dashboard:
      rule: "PathPrefix(`/dashboard`) || PathPrefix(`/api`)"
      service: api@internal
      entryPoints:
        - api

  services:
    dynamic-service:
      loadBalancer:
        servers:
          - url: "http://{best_node.split(':')[0]}:80"
"""

def write_config_file(config_text, path=CONFIG_PATH):
    try:
        with open(path, "w") as f:
            f.write(config_text)
        print(f"[{datetime.now()}] [INFO] Config 파일 저장 완료: {path}")
    except Exception as e:
        print(f"[{datetime.now()}] [ERROR] Config 저장 실패: {e}")

if __name__ == "__main__":
    best_node = get_best_node()
    config_text = generate_dynamic_config(best_node)
    write_config_file(config_text)
