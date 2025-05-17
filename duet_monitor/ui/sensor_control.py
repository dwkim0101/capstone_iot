"""
센서 제어 모듈
"""
import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, List, Optional
from ..core.data_processor import DataProcessor
from ..config.settings import FONT_FAMILY, SENSOR_UNITS

class SensorControl(ttk.LabelFrame):
    def __init__(self, parent: tk.Widget, data_processor: DataProcessor):
        """
        센서 제어 초기화
        
        Args:
            parent: 부모 위젯
            data_processor: 데이터 처리기
        """
        super().__init__(parent, text="센서 제어")
        self.parent = parent
        self.data_processor = data_processor
        
        # 선택된 센서
        self.selected_sensor = None
        
        # UI 초기화
        self.setup_ui()
        
    def setup_ui(self):
        """UI 초기화"""
        # 센서 선택 프레임
        sensor_frame = ttk.LabelFrame(self, text="센서 선택")
        sensor_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 센서 선택 콤보박스
        self.sensor_combo = ttk.Combobox(sensor_frame, state="readonly", width=30)
        self.sensor_combo.pack(fill=tk.X, padx=5, pady=5)
        self.sensor_combo.bind('<<ComboboxSelected>>', self.on_sensor_selected)
        
        # 7세그먼트 디스플레이 프레임
        display_frame = ttk.LabelFrame(self, text="센서 값")
        display_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 7세그먼트 디스플레이 캔버스
        self.canvas = tk.Canvas(display_frame, width=300, height=80, bg='black')
        self.canvas.pack(padx=5, pady=5)
        
        # 7세그먼트 좌표 정의
        self.segments = {
            'top': [(10, 5), (50, 5)],
            'top_left': [(10, 5), (10, 25)],
            'top_right': [(50, 5), (50, 25)],
            'middle': [(10, 25), (50, 25)],
            'bottom_left': [(10, 25), (10, 45)],
            'bottom_right': [(50, 25), (50, 45)],
            'bottom': [(10, 45), (50, 45)]
        }
        
        # 7세그먼트 디스플레이 초기화
        self.setup_segment_display()
        
        # 초기 센서 목록 업데이트
        self.update_sensor_list({})
        
    def on_sensor_selected(self, event=None):
        """센서 선택 이벤트 처리"""
        self.selected_sensor = self.sensor_combo.get()
        
    def get_selected_sensor(self) -> Optional[str]:
        """선택된 센서 반환"""
        return self.selected_sensor
        
    def update_sensor_list(self, values: Dict[str, Any]):
        """센서 목록 업데이트"""
        # 숫자 값을 가진 센서만 필터링
        numeric_sensors = [
            sensor for sensor, value in values.items()
            if isinstance(value, (int, float)) and 
            not isinstance(value, bool)
        ]
        
        # 목록 업데이트
        self.sensor_combo['values'] = numeric_sensors
        
        # 첫 번째 센서 자동 선택
        if numeric_sensors and not self.selected_sensor:
            self.sensor_combo.set(numeric_sensors[0])
            self.on_sensor_selected()
            
    def display_digit(self, position, digit, with_dot=False):
        """특정 위치에 숫자 표시"""
        # 모든 세그먼트를 회색으로 설정
        for seg in self.segments[position].values():
            self.canvas.itemconfig(seg, fill='dark gray')
            
        # 활성화할 세그먼트 설정
        for seg_name in self.digit_segments.get(digit, []):
            if seg_name in self.segments[position]:
                self.canvas.itemconfig(self.segments[position][seg_name], fill='red')
                
        # 소수점 설정
        if 'DOT' in self.segments[position]:
            color = 'red' if with_dot else 'dark gray'
            self.canvas.itemconfig(self.segments[position]['DOT'], fill=color)
            
    def update_display(self, values: Dict[str, Any]):
        """디스플레이 업데이트"""
        if self.selected_sensor and self.selected_sensor in values:
            value = values[self.selected_sensor]
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                unit = SENSOR_UNITS.get(self.selected_sensor, "")
                # 센서에 따라 소수점 자릿수 결정
                decimal_places = self.get_decimal_places(self.selected_sensor, value)
                self.display_value(value, unit, decimal_places)
                
    def get_decimal_places(self, sensor_name: str, value: float) -> int:
        """센서별 소수점 자릿수 결정"""
        # 센서 이름에 따라 소수점 자릿수 결정
        if sensor_name.startswith('temperature') or sensor_name.startswith('temp'):
            # 온도는 소수점 1자리
            return 1
        elif sensor_name.startswith('humidity') or sensor_name.startswith('humi'):
            # 습도는 소수점 없음
            return 0
        elif sensor_name.startswith('pressure') or sensor_name.startswith('pres'):
            # 압력은 소수점 2자리
            return 2
        elif abs(value) < 10:
            # 값이 작은 경우 소수점 2자리
            return 2
        elif abs(value) < 100:
            # 값이 중간인 경우 소수점 1자리
            return 1
        else:
            # 값이 큰 경우 소수점 없음
            return 0
            
    def display_value(self, value, unit="", decimal_places=1):
        """LED 디스플레이에 값 표시"""
        try:
            # 소수점 자릿수에 따라 포맷 설정
            if decimal_places == 0:
                value_str = f"{int(value)}"
                dot_position = None
            elif decimal_places == 1:
                value_str = f"{float(value):.1f}"
                dot_position = 1
            elif decimal_places == 2:
                value_str = f"{float(value):.2f}"
                dot_position = 0
            else:
                value_str = f"{float(value):.1f}"
                dot_position = 1
            
            # 각 자릿수 추출
            digits = []
            for char in value_str:
                if char != '.':
                    digits.append(int(char))
            
            # 4자리 채우기 (왼쪽에 빈 자리는 0으로)
            while len(digits) < 4:
                digits.insert(0, 0)
                
            # 값이 너무 큰 경우 처리
            if len(digits) > 4:
                digits = digits[-4:]
                
            # 각 자릿수 표시
            for i in range(4):
                # 소수점 위치에 따라 소수점 표시
                with_dot = (dot_position is not None and i == dot_position)
                self.display_digit(i, digits[i], with_dot)
                
            # 단위 업데이트
            self.canvas.itemconfig(self.unit_text, text=unit)
            
        except Exception as e:
            print(f"LED 값 표시 오류: {e}")
            # 오류 시 모두 0으로 표시
            for i in range(4):
                self.display_digit(i, 0, i == 1)
                
    def setup_segment_display(self):
        """7세그먼트 디스플레이 초기화"""
        # 각 자리의 세그먼트 생성
        self.segments = {}
        
        # 4자리 디스플레이 생성
        for pos in range(4):
            x_offset = 10 + pos * 60  # 각 자리 사이 간격 감소
            
            # 각 자리의 세그먼트 좌표 계산
            self.segments[pos] = {
                'A': self.canvas.create_line(x_offset+5, 10, x_offset+40, 10, width=2, fill='dark gray'),  # 선 두께 감소
                'B': self.canvas.create_line(x_offset+40, 15, x_offset+40, 35, width=2, fill='dark gray'),
                'C': self.canvas.create_line(x_offset+40, 40, x_offset+40, 60, width=2, fill='dark gray'),
                'D': self.canvas.create_line(x_offset+5, 65, x_offset+40, 65, width=2, fill='dark gray'),
                'E': self.canvas.create_line(x_offset+5, 40, x_offset+5, 60, width=2, fill='dark gray'),
                'F': self.canvas.create_line(x_offset+5, 15, x_offset+5, 35, width=2, fill='dark gray'),
                'G': self.canvas.create_line(x_offset+5, 35, x_offset+40, 35, width=2, fill='dark gray'),
            }
            
            # 모든 자리에 소수점 추가
            self.segments[pos]['DOT'] = self.canvas.create_oval(
                x_offset+45, 55, x_offset+50, 60, fill='dark gray', outline='dark gray'  # 소수점 크기 감소
            )
                
        # 단위 표시 텍스트
        self.unit_text = self.canvas.create_text(
            250, 30, text="", fill="white", font=(FONT_FAMILY, 10)  # 폰트 크기 감소
        )
        
        # 숫자별 세그먼트 패턴 정의
        self.digit_segments = {
            0: ['A', 'B', 'C', 'D', 'E', 'F'],
            1: ['B', 'C'],
            2: ['A', 'B', 'D', 'E', 'G'],
            3: ['A', 'B', 'C', 'D', 'G'],
            4: ['B', 'C', 'F', 'G'],
            5: ['A', 'C', 'D', 'F', 'G'],
            6: ['A', 'C', 'D', 'E', 'F', 'G'],
            7: ['A', 'B', 'C'],
            8: ['A', 'B', 'C', 'D', 'E', 'F', 'G'],
            9: ['A', 'B', 'C', 'D', 'F', 'G']
        }
        
        # 초기값 표시
        self.display_value(0.0) 