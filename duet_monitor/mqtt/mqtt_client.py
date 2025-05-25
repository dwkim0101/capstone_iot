"""
MQTT 클라이언트 모듈
"""
import json
import requests
from typing import Optional, Any
from duet_monitor.utils.debug import debug_print_main
from duet_monitor.mqtt.mqtt_snapshot_handler import MQTTSnapshotHandler

last_mqtt_response: Optional[str] = None
last_mqtt_status_code: Optional[int] = None
_snapshot_handler: Optional[MQTTSnapshotHandler] = None
_snapshot_handler: Optional[MQTTSnapshotHandler] = None

def init_snapshot_handler(token: str, serial_number: str, snapshot_interval: int = 3600):
    """스냅샷 핸들러 초기화"""
    global _snapshot_handler
    if _snapshot_handler is None:
        _snapshot_handler = MQTTSnapshotHandler(token, serial_number, snapshot_interval)
        debug_print_main("[MQTT] 스냅샷 핸들러 초기화됨")

def cleanup_snapshot_handler():
    """스냅샷 핸들러 정리"""
    global _snapshot_handler
    if _snapshot_handler is not None:
        _snapshot_handler = None
        debug_print_main("[MQTT] 스냅샷 핸들러 정리됨")

def mqtt_publish_only(topic: str, payload: Any, token: Optional[str] = None):
    """MQTT 메시지 발행 및 스냅샷 데이터 수집"""
    global last_mqtt_response, last_mqtt_status_code, _snapshot_handler
    
    last_mqtt_status_code = None
    last_mqtt_response = None
    
    try:
        # 페이로드 처리
        payload_data = payload
        if isinstance(payload, str):
            try:
                payload_data = json.loads(payload)
            except json.JSONDecodeError:
                debug_print_main("[MQTT] JSON 파싱 실패, 원본 데이터 사용")
        
        # 스냅샷 데이터 수집
        if _snapshot_handler is not None:
            _snapshot_handler.add_data_point(payload_data)
            debug_print_main("[MQTT] 스냅샷용 데이터 포인트 추가됨")
        
        # MQTT 메시지 전송
        url = "https://smartair.site/mqtt/receive"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "*/*"
        }
        data = {"topic": topic, "payload": payload}
        
        debug_print_main(f"[MQTT-REST] POST 요청 시작: {url}")
        
        response = requests.post(url, headers=headers, json=data, timeout=5)
        last_mqtt_status_code = response.status_code
        last_mqtt_response = response.text
        
        debug_print_main(f"[MQTT-REST] 응답 코드: {last_mqtt_status_code}")
        debug_print_main(f"[MQTT-REST] 응답 본문: {last_mqtt_response}")
        
        return response.status_code == 200
        
    except requests.exceptions.Timeout:
        last_mqtt_status_code = 598
        last_mqtt_response = "MQTT 서버 응답 시간 초과"
        debug_print_main(f"[MQTT-REST 예외] {last_mqtt_response}")
        return False
        
    except requests.exceptions.ConnectionError:
        last_mqtt_status_code = 599
        last_mqtt_response = "MQTT 서버 연결 실패"
        debug_print_main(f"[MQTT-REST 예외] {last_mqtt_response}")
        return False
        
    except Exception as e:
        last_mqtt_status_code = 500
        last_mqtt_response = f"예외 발생: {str(e)}"
        debug_print_main(f"[MQTT-REST 예외] {last_mqtt_response}")
        return False