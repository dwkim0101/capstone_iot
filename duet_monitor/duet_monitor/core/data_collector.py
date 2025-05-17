"""
데이터 수집 모듈
"""
import serial
import json
import time
from typing import Optional, Dict, Any, Tuple
from queue import Queue
from duet_monitor.utils.helpers import fix_json_string

class DataCollector:
    def __init__(self, port: str, baud_rate: int = 115200):
        """
        데이터 수집기 초기화
        
        Args:
            port: 시리얼 포트
            baud_rate: 통신 속도
        """
        self.port = port
        self.baud_rate = baud_rate
        self.serial_port: Optional[serial.Serial] = None
        self.is_running = False
        self.data_queue = Queue()
        self.buffer = ""
        self.last_read_time = 0
        self.max_buffer_size = 10000  # 최대 버퍼 크기 (10KB)
        
    def start(self) -> bool:
        """
        데이터 수집 시작
        
        Returns:
            bool: 성공 여부
        """
        try:
            self.serial_port = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=0.1
            )
            self.is_running = True
            return True
        except Exception as e:
            print(f"시리얼 포트 연결 실패: {e}")
            return False
            
    def stop(self):
        """데이터 수집 중지"""
        self.is_running = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.serial_port = None
            
    def collect_data(self):
        """데이터 수집 메인 루프"""
        while self.is_running:
            try:
                if not self.serial_port or not self.serial_port.is_open:
                    print("시리얼 포트가 열려있지 않습니다.")
                    time.sleep(1)
                    continue
                    
                # 버퍼 크기 제한
                if len(self.buffer) > self.max_buffer_size:
                    self.buffer = self.buffer[-self.max_buffer_size:]
                    
                # 데이터 읽기
                if self.serial_port.in_waiting:
                    chunk = self.serial_port.read(min(1024, self.serial_port.in_waiting))
                    self.buffer += chunk.decode('utf-8')
                    self.last_read_time = time.time()
                    
                # JSON 파싱
                while '\n' in self.buffer:
                    line, self.buffer = self.buffer.split('\n', 1)
                    line = line.strip()
                    
                    if not line:
                        continue
                        
                    try:
                        data = json.loads(line)
                        self.data_queue.put(data)
                    except json.JSONDecodeError:
                        # JSON 복구 시도
                        fixed_json, is_fixed, method, error = fix_json_string(line)
                        if is_fixed:
                            try:
                                data = json.loads(fixed_json)
                                data['_fixed'] = True
                                data['_recovery_method'] = method
                                data['_original_error'] = error
                                self.data_queue.put(data)
                            except json.JSONDecodeError:
                                print(f"복구된 JSON 파싱 실패: {error}")
                        else:
                            print(f"JSON 복구 실패: {error}")
                            
                # CPU 부하 감소
                time.sleep(0.001)
                
            except Exception as e:
                print(f"데이터 수집 오류: {e}")
                time.sleep(1)
                
    def get_data(self) -> Optional[Dict[str, Any]]:
        """
        큐에서 데이터 가져오기
        
        Returns:
            Optional[Dict[str, Any]]: 데이터 또는 None
        """
        try:
            return self.data_queue.get_nowait()
        except:
            return None 