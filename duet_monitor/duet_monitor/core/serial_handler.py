"""
시리얼 통신 핸들러 모듈
"""
import serial
import serial.tools.list_ports
import time
import json
import threading
from typing import Dict, Any, Optional, Callable, List
from queue import Queue
import datetime

from duet_monitor.config.settings import TIMEOUT, DEFAULT_PORT, DEFAULT_BAUD_RATE, SERIAL_TIMEOUT
from duet_monitor.utils.helpers import fix_json_string

# MQTT 연동 예시 (메인에서 콜백에 넘겨 사용)
# from duet_monitor.mqtt.mqtt_client import publish_mqtt
# def on_serial_data(data):
#     publish_mqtt(token, topic, data, broker, port)
# handler = SerialHandler(data_callback=on_serial_data)

class SerialHandler:
    def __init__(self, data_callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        """
        시리얼 핸들러 초기화
        
        Args:
            data_callback: 데이터 수신 콜백 함수
        """
        self.serial_port: Optional[serial.Serial] = None
        self.port_name: Optional[str] = None
        self.baud_rate: int = 0
        self.is_connected: bool = False
        self.is_reading: bool = False
        self.read_thread: Optional[threading.Thread] = None
        self.data_callback = data_callback
        self.data_queue: Queue = Queue()
        
        # 버퍼 관련 설정
        self.buffer: str = ""
        self.max_buffer_size: int = 10000  # 최대 버퍼 크기 (10KB)
        
    def connect(self, port: str, baud_rate: int) -> bool:
        """
        시리얼 포트 연결
        
        Args:
            port: 포트 이름
            baud_rate: 통신 속도
            
        Returns:
            bool: 성공 여부
        """
        if self.is_connected:
            self.close()
            
        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=baud_rate,
                timeout=TIMEOUT
            )
            
            self.port_name = port
            self.baud_rate = baud_rate
            self.is_connected = True
            
            print(f"시리얼 포트 연결됨: {port} ({baud_rate})")
            return True
            
        except Exception as e:
            print(f"시리얼 포트 연결 실패: {e}")
            self.is_connected = False
            return False
            
    def close(self) -> bool:
        """
        시리얼 포트 연결 해제
        
        Returns:
            bool: 성공 여부
        """
        # 데이터 읽기 중단
        if self.is_reading:
            self.stop_reading()
            
        # 포트 닫기
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
                self.is_connected = False
                self.port_name = None
                self.baud_rate = 0
                print("시리얼 포트 연결 해제됨")
                return True
                
            except Exception as e:
                print(f"시리얼 포트 연결 해제 실패: {e}")
                return False
                
        return True
        
    def start_reading(self) -> bool:
        """
        데이터 읽기 시작
        
        Returns:
            bool: 성공 여부
        """
        if not self.is_connected or not self.serial_port or not self.serial_port.is_open:
            print("시리얼 포트가 연결되지 않았습니다.")
            return False
            
        if self.is_reading:
            print("이미 데이터를 읽고 있습니다.")
            return True
            
        # 버퍼 초기화
        self.buffer = ""
        
        # 읽기 시작
        self.is_reading = True
        self.read_thread = threading.Thread(target=self._read_data, daemon=True)
        self.read_thread.start()
        
        print("데이터 읽기 시작됨")
        return True
        
    def stop_reading(self) -> bool:
        """
        데이터 읽기 중단
        
        Returns:
            bool: 성공 여부
        """
        if not self.is_reading:
            print("데이터를 읽고 있지 않습니다.")
            return True
            
        self.is_reading = False
        
        # 스레드 종료 대기
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=2.0)
            
        print("데이터 읽기 중단됨")
        return True
        
    def _read_data(self):
        """데이터 읽기 스레드"""
        while self.is_reading and self.serial_port and self.serial_port.is_open:
            try:
                # 버퍼 크기 제한
                if len(self.buffer) > self.max_buffer_size:
                    # 마지막으로 발견된 JSON 시작 부분부터 유지
                    last_brace = self.buffer.rfind('{')
                    if last_brace >= 0:
                        self.buffer = self.buffer[last_brace:]
                    else:
                        self.buffer = self.buffer[-self.max_buffer_size:]
                    
                # 데이터 읽기
                if self.serial_port.in_waiting > 0:
                    chunk = self.serial_port.read(min(1024, self.serial_port.in_waiting))
                    try:
                        self.buffer += chunk.decode('utf-8', errors='replace')
                    except UnicodeDecodeError as e:
                        print(f"디코딩 오류: {e}")
                        continue
                    
                # JSON 데이터 파싱
                self._parse_json()
                    
                # 잠시 대기
                time.sleep(0.01)
                
            except Exception as e:
                print(f"데이터 읽기 오류: {e}")
                self.is_reading = False
                break
                
    def _parse_json(self):
        """JSON 데이터 파싱"""
        # 라인 단위로 분리
        while '\n' in self.buffer:
            line, self.buffer = self.buffer.split('\n', 1)
            line = line.strip()
            
            if not line:
                continue
                
            # JSON 파싱 시도
            try:
                data = json.loads(line)
                self._process_data(data)
                
            except json.JSONDecodeError:
                # JSON 복구 시도
                fixed_json, is_fixed, method, error = fix_json_string(line)
                if is_fixed:
                    try:
                        data = json.loads(fixed_json)
                        data['_fixed'] = True
                        data['_fix_method'] = method
                        data['_original_error'] = str(error)
                        self._process_data(data)
                    except json.JSONDecodeError as e:
                        print(f"복구된 JSON 파싱 실패: {str(e)}")
                else:
                    print(f"JSON 복구 실패: {str(error)} - {line}")
                    
    def _process_data(self, data: Dict[str, Any]):
        """
        데이터 처리
        
        Args:
            data: 수신된 데이터
        """
        # 타임스탬프 추가
        if 'timestamp' not in data:
            data['timestamp'] = datetime.datetime.now()
            
        # 데이터 큐에 추가
        self.data_queue.put(data)
        
        # 콜백 함수 호출
        if self.data_callback:
            try:
                from duet_monitor.utils.debug import debug_print_main
                print(f"[serial_handler:_process_data] 콜백 호출 직전: {data}")
                debug_print_main(f"[serial_handler:_process_data] 콜백 호출 직전: {data}")
                # timestamp가 datetime이면 문자열로 변환
                if 'timestamp' in data and hasattr(data['timestamp'], 'isoformat'):
                    data['timestamp'] = data['timestamp'].isoformat()
            except Exception as e:
                print(f"[serial_handler:_process_data] 콜백 직전 예외: {e}")
                pass
            self.data_callback(data)
            
    def get_data(self) -> Optional[Dict[str, Any]]:
        """
        수신된 데이터 가져오기
        
        Returns:
            Optional[Dict[str, Any]]: 수신된 데이터 (없으면 None)
        """
        if self.data_queue.empty():
            return None
            
        return self.data_queue.get()
        
    def get_available_ports() -> List[str]:
        """
        사용 가능한 시리얼 포트 목록 반환
        
        Returns:
            List[str]: 포트 목록
        """
        return [port.device for port in serial.tools.list_ports.comports()] 