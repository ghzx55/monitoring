import requests
from datetime import datetime
import time
import os

# Main node의 Prometheus 대시보드 경로
PROMETHEUS_URL = "http://211.183.3.200:9090"

# 물리 자원에 대한 쿼리 정의
CPU_QUERY = '100 - avg by(instance)(rate(node_cpu_seconds_total{mode="idle"}[15s])) * 100'
RAM_QUERY = '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100'

# 동적 라우팅 설정 파일 경로
CONFIG_PATH = "/etc/traefik/dynamic_conf.yml"

def query_prometheus(query):
    try:
        res = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": query})
        res.raise_for_status()
        return res.json()["data"]["result"]
    except Exception as e:
        print(f"[ERROR] Prometheus query failed: {e}")
        return []

# CPU 사용량 출력
def get_cpu_usages():
    result = query_prometheus(CPU_QUERY)
    return {item["metric"]["instance"]: float(item["value"][1]) for item in result}

# RAM 사용량 출력
def get_ram_usages():
    result = query_prometheus(RAM_QUERY)
    return {item["metric"]["instance"]: float(item["value"][1]) for item in result}

def get_best_node():
    cpu_usages = get_cpu_usages()
    ram_usages = get_ram_usages()

    if not cpu_usages or not ram_usages:
        print("[ERROR] Failed to fetch resource data from Prometheus.")
        return None
    
    # CPU와 RAM을 고려한 node들의 가용 점수 계산
    scores = {}

    # CPU와 RAM에 대한 가중치 설정
    cpu_weight = 0.8
    ram_weight = 0.2

    for instance in cpu_usages:
        cpu = cpu_usages.get(instance, 100)
        ram = ram_usages.get(instance, 100)
        score = (100 - cpu) * cpu_weight + (100 - ram) * ram_weight
        scores[instance] = score
        print(f"[INFO] {instance} → CPU: {cpu:.1f}%, RAM: {ram:.1f}%, SCORE: {score:.1f}")

    best_node = max(scores.items(), key=lambda x: x[1])
    print(f"[INFO] Idle node: {best_node[0]} (SCORE: {best_node[1]:.2f})")
    return best_node[0]

# dynamic_conf.yml 생성
def generate_dynamic_config():
    best_node = get_best_node()

    if best_node and ":" in best_node:
        best_ip = best_node.split(":")[0]
    else:
        best_ip = best_node or "localhost"

    print(f"[DEBUG] Best IP: {best_ip}")

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
          - url: "http://{best_ip}:8020"
"""

def write_config_file(config_text, path=CONFIG_PATH):
    try:
        with open(path, "w") as f:
            f.write(config_text)
            f.flush()
            os.fsync(f.fileno())
        print(f"[{datetime.now()}] [INFO] Config file save complete: {path}")
    except Exception as e:
        print(f"[{datetime.now()}] [ERROR] Config file save failed: {e}")

if __name__ == "__main__":
    config_text = generate_dynamic_config()
    write_config_file(config_text)
