import serial
import json
import requests
import time

# 시리얼 포트 설정
ser = serial.Serial('/dev/ttyUSB0', 9600)  # 포트와 속도는 환경에 맞게 조정

# 서버 URL
SERVER_URL = "https://your-server.com/api/data"

while True:
    if ser.in_waiting > 0:
        line = ser.readline().decode('utf-8').strip()
        try:
            data = json.loads(line)
            # 서버로 전송
            response = requests.post(SERVER_URL, json=data)
            print(f"데이터 전송: {response.status_code}")
        except json.JSONDecodeError:
            print("JSON 파싱 오류:", line)
        except Exception as e:
            print("오류 발생:", str(e))
    time.sleep(0.1)
