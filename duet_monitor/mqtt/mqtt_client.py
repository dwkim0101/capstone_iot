import json
impordef mqtt_publish_only(topic, payload, token=None):
    global last_mqtt_response
    global last_mqtt_status_code
    global _snapshot_handler
    
    last_mqtt_status_code = None
    last_mqtt_response = None
    
    try:
        # 페이로드가 유효한 JSON 형식인지 확인
        if isinstance(payload, str):
            try:
                payload_data = json.loads(payload)
            except json.JSONDecodeError:
                payload_data = payload
        else:
            payload_data = payload

        # 스냅샷 핸들러가 초기화되어 있다면 데이터 추가
        if _snapshot_handler is not None:
            _snapshot_handler.add_data_point(payload_data)
            debug_print_main("[MQTT] 스냅샷용 데이터 포인트 추가됨")

        url = "https://smartair.site/mqtt/receive"  # 실제 서비스 주소로 변경 필요sts
from typing import Optional
from duet_monitor.utils.debug import debug_print_main
from duet_monitor.mqtt.mqtt_snapshot_handler import MQTTSnapshotHandler

last_mqtt_response = None
last_mqtt_status_code = None
_snapshot_handler: Optional[MQTTSnapshotHandler] = None

def init_snapshot_handler(token: str, serial_number: str, snapshot_interval: int = 3600):
    """스냅샷 핸들러 초기화"""
    global _snapshot_handler
    if _snapshot_handler is None:
        _snapshot_handler = MQTTSnapshotHandler(token, serial_number, snapshot_interval)
        debug_print_main("[MQTT] 스냅샷 핸들러 초기화됨")

def mqtt_publish_only(topic, payload, token=None):
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