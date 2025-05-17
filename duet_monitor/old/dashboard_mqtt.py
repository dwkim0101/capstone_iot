import requests
import paho.mqtt.client as mqtt
import time
from dashboard_auth import DashboardAuth

# 환경설정 (필요에 따라 수정)
DASHBOARD_API_URL = "https://smartair.site/api/your-endpoint"  # 실제 엔드포인트로 변경
MQTT_BROKER = "mqtt.broker.address"  # 실제 브로커 주소로 변경
MQTT_PORT = 1883
MQTT_TOPIC = "your/topic"  # 실제 토픽으로 변경
INTERVAL = 60  # 데이터 전송 주기(초)

# 인증 정보 (실제 계정 정보로 변경)
EMAIL = "your_email@example.com"
PASSWORD = "your_password"
NAME = "홍길동"

def fetch_dashboard_data(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(DASHBOARD_API_URL, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print("대시보드 데이터 조회 실패:", response.status_code, response.text)
        return None

def send_mqtt(data):
    client = mqtt.Client()
    # client.username_pw_set("username", "password")  # 필요시
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.publish(MQTT_TOPIC, payload=str(data))
    client.disconnect()

def main():
    auth = DashboardAuth(EMAIL, PASSWORD, NAME)
    token = auth.get_token()
    if not token:
        print("토큰 발급 실패. 종료합니다.")
        return
    while True:
        data = fetch_dashboard_data(token)
        if data:
            send_mqtt(data)
            print("MQTT로 데이터 전송 완료.")
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main() 