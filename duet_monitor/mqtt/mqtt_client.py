import json
import requests
from duet_monitor.utils.debug import debug_print_main

last_mqtt_response = None
last_mqtt_status_code = None

def mqtt_publish_only( topic, payload, token=None):
    global last_mqtt_response
    global last_mqtt_status_code
    last_mqtt_status_code = None
    last_mqtt_response = None
    try:
        url = "https://smartair.site/mqtt/receive"  # 실제 서비스 주소로 변경 필요
        headers = {
            "Authorization": f'Bearer {token}',
            "Content-Type": "application/json",
            "accept": "*/*"
        }
        data = {
            "topic": topic,
            "payload": payload
        }
        debug_print_main(f"[MQTT-REST] POST 요청 시작: {url}")
        debug_print_main(f"[MQTT-REST] 요청 헤더: {headers}")
        debug_print_main(f"[MQTT-REST] POST BODY: {data}")
        debug_print_main(f"[MQTT-REST] 요청 데이터: {data}")
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=5)
            if resp is not None:
                debug_print_main(f"[MQTT-REST] 응답 코드: {resp.status_code}")
                debug_print_main(f"[MQTT-REST] 응답 본문: {resp.text}")
                last_mqtt_response = resp.text
                last_mqtt_status_code = resp.status_code
            else:
                last_mqtt_status_code = 500
                last_mqtt_response = "MQTT 서버 응답 없음 (resp is None)"
                debug_print_main(f"[MQTT-REST] 응답 없음: resp is None")
        except requests.exceptions.Timeout:
            last_mqtt_status_code = 598
            last_mqtt_response = "MQTT 서버 응답 시간 초과"
            debug_print_main(f"[MQTT-REST 예외] Timeout: {last_mqtt_response}")
        except requests.exceptions.ConnectionError:
            last_mqtt_status_code = 599
            last_mqtt_response = "MQTT 서버 연결 실패"
            debug_print_main(f"[MQTT-REST 예외] ConnectionError: {last_mqtt_response}")
    except Exception as e:
        debug_print_main(f"[MQTT-REST 예외] {e}")
        last_mqtt_status_code = 500
        last_mqtt_response = f"예외 발생: {e}"
    debug_print_main(f"[MQTT-REST][마지막] last_mqtt_status_code: {last_mqtt_status_code}, last_mqtt_response: {last_mqtt_response}") 