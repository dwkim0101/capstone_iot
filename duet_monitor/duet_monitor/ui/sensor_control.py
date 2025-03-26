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
        self.canvas = tk.Canvas(display_frame, width=300, height=100, bg='black')
        self.canvas.pack(padx=5, pady=5)
        
        # 7세그먼트 좌표 정의
        self.segments = {
            'top': [(50, 20), (250, 20)],
            'top_left': [(50, 20), (50, 80)],
            'top_right': [(250, 20), (250, 80)],
            'middle': [(50, 80), (250, 80)],
            'bottom_left': [(50, 80), (50, 140)],
            'bottom_right': [(250, 80), (250, 140)],
            'bottom': [(50, 140), (250, 140)]
        }
        
        # 7세그먼트 디스플레이 초기화
        self.setup_segment_display()
        
        # 그래프 선택 프레임
        graph_frame = ttk.LabelFrame(self, text="그래프 설정")
        graph_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 그래프 선택 콤보박스
        self.graph_combo = ttk.Combobox(graph_frame, state="readonly", width=30)
        self.graph_combo.pack(fill=tk.X, padx=5, pady=5)
        self.graph_combo.bind('<<ComboboxSelected>>', self.on_graph_selected)
        
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
        if position == 1 and 'DOT' in self.segments[position]:
            color = 'red' if with_dot else 'dark gray'
            self.canvas.itemconfig(self.segments[position]['DOT'], fill=color)
            
    def display_value(self, value, unit=""):
        """LED 디스플레이에 값 표시"""
        try:
            # 값을 문자열로 변환하고 소수점 이하 1자리로 반올림
            value_str = f"{float(value):.1f}"
            
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
                self.display_digit(i, digits[i], i == 1)  # 두 번째 자리에 소수점
                
            # 단위 업데이트
            self.canvas.itemconfig(self.unit_text, text=unit)
            
        except Exception as e:
            print(f"LED 값 표시 오류: {e}")
            # 오류 시 모두 0으로 표시
            for i in range(4):
                self.display_digit(i, 0, i == 1)
                
    def update_display(self, values: Dict[str, Any]):
        """디스플레이 업데이트"""
        if self.selected_sensor and self.selected_sensor in values:
            value = values[self.selected_sensor]
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                unit = SENSOR_UNITS.get(self.selected_sensor, "")
                self.display_value(value, unit)

    def on_graph_selected(self, event=None):
        """그래프 선택 이벤트 핸들러"""
        selected_sensor = self.graph_combo.get()
        if selected_sensor:
            self.data_processor.set_selected_graph_sensor(selected_sensor)

    def setup_segment_display(self):
        """7세그먼트 디스플레이 초기화"""
        # 각 자리의 세그먼트 생성
        self.segments = {}
        
        # 4자리 디스플레이 생성
        for pos in range(4):
            x_offset = 20 + pos * 80  # 각 자리 사이 간격
            
            # 각 자리의 세그먼트 좌표 계산
            self.segments[pos] = {
                'A': self.canvas.create_line(x_offset+10, 20, x_offset+60, 20, width=5, fill='dark gray'),
                'B': self.canvas.create_line(x_offset+60, 25, x_offset+60, 55, width=5, fill='dark gray'),
                'C': self.canvas.create_line(x_offset+60, 65, x_offset+60, 95, width=5, fill='dark gray'),
                'D': self.canvas.create_line(x_offset+10, 100, x_offset+60, 100, width=5, fill='dark gray'),
                'E': self.canvas.create_line(x_offset+10, 65, x_offset+10, 95, width=5, fill='dark gray'),
                'F': self.canvas.create_line(x_offset+10, 25, x_offset+10, 55, width=5, fill='dark gray'),
                'G': self.canvas.create_line(x_offset+10, 60, x_offset+60, 60, width=5, fill='dark gray'),
            }
            
            # 두 번째 자리에 소수점 추가
            if pos == 1:
                self.segments[pos]['DOT'] = self.canvas.create_oval(
                    x_offset+65, 90, x_offset+75, 100, fill='dark gray', outline='dark gray'
                )
                
        # 단위 표시 텍스트
        self.unit_text = self.canvas.create_text(
            280, 50, text="", fill="white", font=(FONT_FAMILY, 12)
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