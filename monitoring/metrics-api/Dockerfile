FROM python:3.10

WORKDIR /app

# Flask, Requests 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# main.py, scheduler.py 복사
COPY . .

# Flask 서버 실행 명령
CMD ["python", "main.py"]
