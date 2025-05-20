"""
LED 디스플레이 모듈
"""
import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional, List
from duet_monitor.config.settings import LED_COLORS, LED_SIZE
from duet_monitor.utils.helpers import get_unit_for_sensor

class LedDisplay(ttk.LabelFrame):
    def __init__(self, parent: tk.Widget):
        """
        LED 디스플레이 초기화
        
        Args:
            parent: 부모 위젯
        """
        super().__init__(parent, text="센서 값 LED 디스플레이")
        self.parent = parent
        
        # LED 디스플레이 설정
        self.segments = {}
        self.digit_width = 15
        self.digit_height = 30
        self.digit_spacing = 5
        self.dot_size = 5
        
        # 선택된 센서와 값
        self.selected_sensor = None
        self.displayed_value = 0.0
        self.displayed_unit = ""
        
        # 기본 LED 설정
        self.leds = {}
        self.led_labels = {}
        self.available_sensors = []
        
        # 상태 표시 LED
        self.status_led = None
        self.is_active = False
        
        # UI 초기화
        self.setup_ui()
        
        # 테스트 데이터로 초기화
        self.initialized = False
        
    def setup_ui(self):
        """UI 초기화"""
        # 기본 LED 디스플레이 설정
        self.setup_basic_led()
        
        # 상태 표시 프레임
        self.status_frame = ttk.Frame(self)
        self.status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 상태 레이블
        ttk.Label(self.status_frame, text="수집 상태:").pack(side=tk.LEFT, padx=5)
        
        # 상태 LED 생성
        self.status_canvas = tk.Canvas(self.status_frame, width=LED_SIZE, height=LED_SIZE, bg='white', highlightthickness=1)
        self.status_canvas.pack(side=tk.LEFT, padx=5)
        
        # LED 원 그리기
        self.status_led = self.status_canvas.create_oval(2, 2, LED_SIZE-2, LED_SIZE-2, fill='gray')
        
    def setup_basic_led(self):
        """기본 LED 표시 설정"""
        # LED 패널
        self.led_frame = ttk.Frame(self)
        self.led_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # LED 그리드
        self.led_grid = ttk.Frame(self.led_frame)
        self.led_grid.pack(fill=tk.BOTH, expand=True)
        
        # LED 크기 설정
        self.digit_width = 15  # 더 작은 크기로 조정
        self.digit_height = 8  # 더 작은 크기로 조정
        
        # LED 색상 설정
        self.on_color = "#00ff00"  # 켜진 상태 색상
        self.off_color = "#003300"  # 꺼진 상태 색상
        
        # LED 상태 저장
        self.leds = {}
        
        # 센서 목록이 비어있을 때 표시할 메시지
        self.placeholder = ttk.Label(
            self.led_grid,
            text="센서를 선택하세요",
            font=("AppleGothic", 10)
        )
        self.placeholder.pack(pady=10)
        
    def create_led_display(self):
        """7-세그먼트 LED 디스플레이 생성"""
        # LED 디스플레이 캔버스
        self.led_canvas = tk.Canvas(
            self.display_frame, 
            width=6 * (self.digit_width + self.digit_spacing) + 100,  # 4개 숫자 + 소수점 + 단위
            height=self.digit_height + 40,
            bg="black"
        )
        self.led_canvas.pack(fill=tk.BOTH, expand=True)
        
        # 7-세그먼트 정의 (각 세그먼트의 상대 좌표)
        # A: 상단 가로선, B: 오른쪽 상단 세로선, C: 오른쪽 하단 세로선
        # D: 하단 가로선, E: 왼쪽 하단 세로선, F: 왼쪽 상단 세로선, G: 중앙 가로선
        self.segments_coords = {
            'A': [(1, 1), (self.digit_width-1, 1)],
            'B': [(self.digit_width-1, 1), (self.digit_width-1, self.digit_height//2)],
            'C': [(self.digit_width-1, self.digit_height//2), (self.digit_width-1, self.digit_height-1)],
            'D': [(1, self.digit_height-1), (self.digit_width-1, self.digit_height-1)],
            'E': [(1, self.digit_height//2), (1, self.digit_height-1)],
            'F': [(1, 1), (1, self.digit_height//2)],
            'G': [(1, self.digit_height//2), (self.digit_width-1, self.digit_height//2)]
        }
        
        # 숫자별 세그먼트 구성
        self.digit_segments = {
            0: ['A', 'B', 'C', 'D', 'E', 'F'],
            1: ['B', 'C'],
            2: ['A', 'B', 'D', 'E', 'G'],
            3: ['A', 'B', 'C', 'D', 'G'],
            4: ['B', 'C', 'F', 'G'],
            5: ['A', 'C', 'D', 'F', 'G'],
            5: ['A', 'C', 'D', 'E', 'F', 'G'],
            7: ['A', 'B', 'C'],
            8: ['A', 'B', 'C', 'D', 'E', 'F', 'G'],
            9: ['A', 'B', 'C', 'D', 'F', 'G']
        }
        
        # 4자리 숫자 위치 (소수점 포함)
        self.digit_positions = []
        for i in range(4):
            x_offset = 10 + i * (self.digit_width + self.digit_spacing)
            self.digit_positions.append(x_offset)
            
        # 각 자리별 세그먼트 생성
        for pos_idx in range(4):
            pos_x = self.digit_positions[pos_idx]
            segments = {}
            
            # 각 세그먼트 생성
            for seg_name, coords in self.segments_coords.items():
                # 세그먼트의 좌표 계산
                x1, y1 = coords[0]
                x2, y2 = coords[1]
                
                # 캔버스에 세그먼트 추가
                seg_id = self.led_canvas.create_line(
                    pos_x + x1, y1 + 10,
                    pos_x + x2, y2 + 10,
                    width=3, fill='dark gray'
                )
                segments[seg_name] = seg_id
                
            # 소수점 생성 (2번째 위치 이후에)
            if pos_idx == 1:  # 소수점 위치 (첫째 자리와 둘째 자리 사이)
                dot_x = pos_x + self.digit_width + 2
                dot_y = self.digit_height + 5
                dot_id = self.led_canvas.create_oval(
                    dot_x, dot_y,
                    dot_x + self.dot_size, dot_y + self.dot_size,
                    fill='dark gray', outline='dark gray'
                )
                segments['DOT'] = dot_id
                
            self.segments[pos_idx] = segments
            
        # 단위 표시 텍스트
        self.unit_text = self.led_canvas.create_text(
            10 + 4 * (self.digit_width + self.digit_spacing) + 20,
            self.digit_height // 2 + 10,
            text="", fill="red", font=("Arial", 14)
        )
        
        # 초기값 표시
        self.display_value(0.0, "")
    
    def display_digit(self, position, digit, with_dot=False):
        """
        특정 위치에 숫자 표시
        
        Args:
            position: 표시 위치 (0-3)
            digit: 표시할 숫자 (0-9)
            with_dot: 소수점 표시 여부
        """
        # 모든 세그먼트를 회색으로 설정
        for seg in self.segments[position].values():
            self.led_canvas.itemconfig(seg, fill='dark gray')
            
        # 활성화할 세그먼트 설정
        for seg_name in self.digit_segments.get(digit, []):
            if seg_name in self.segments[position]:
                self.led_canvas.itemconfig(self.segments[position][seg_name], fill='red')
                
        # 소수점 설정
        if position == 1 and 'DOT' in self.segments[position]:  # 소수점 위치
            color = 'red' if with_dot else 'dark gray'
            self.led_canvas.itemconfig(self.segments[position]['DOT'], fill=color)
    
    def display_value(self, value, unit=""):
        """
        LED 디스플레이에 값 표시
        
        Args:
            value: 표시할 값
            unit: 단위
        """
        try:
            # 값을 문자열로 변환하고 소수점 이하 1자리로 반올림
            value_str = f"{float(value):.1f}"
            
            # 소수점 위치 찾기
            dot_pos = value_str.find('.')
            
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
            self.led_canvas.itemconfig(self.unit_text, text=unit)
            
            # 저장
            self.displayed_value = float(value)
            self.displayed_unit = unit
            
        except Exception as e:
            print(f"LED 값 표시 오류: {e}")
            # 오류 시 모두 0으로 표시
            for i in range(4):
                self.display_digit(i, 0, i == 1)
                
    def create_basic_leds(self, sensor_names: List[str]):
        """
        기본 LED 디스플레이 생성
        
        Args:
            sensor_names: 센서 이름 목록
        """
        try:
            # 기존 LED 위젯 정리
            for widget in self.led_grid.winfo_children():
                widget.destroy()
                
            self.leds = {}
            self.led_labels = {}
            
            if not sensor_names:
                # 센서가 없을 경우 메시지 표시
                ttk.Label(self.led_grid, text="사용 가능한 센서가 없습니다").grid(
                    row=0, column=0, padx=10, pady=20
                )
                return
                
            # 센서별 LED 생성 (세로로 배치)
            for i, name in enumerate(sensor_names):
                # 센서 이름 레이블
                name_label = ttk.Label(self.led_grid, text=f"{name}:", width=15, anchor=tk.W)
                name_label.grid(row=i, column=0, padx=5, pady=5, sticky=tk.W)
                
                # LED 캔버스
                canvas = tk.Canvas(self.led_grid, width=LED_SIZE, height=LED_SIZE, 
                                  bg='white', highlightthickness=1)
                canvas.grid(row=i, column=1, padx=5, pady=5)
                
                # LED 원 그리기
                led = canvas.create_oval(2, 2, LED_SIZE-2, LED_SIZE-2, fill='gray')
                self.leds[name] = (canvas, led)  # 캔버스와 LED 객체를 튜플로 저장
                
                # 값 표시 레이블
                value_label = ttk.Label(self.led_grid, text="0.0", width=10, anchor=tk.W)
                value_label.grid(row=i, column=2, padx=5, pady=5, sticky=tk.W)
                self.led_labels[name] = value_label
                
            # 초기화 완료 표시
            self.initialized = True
        except Exception as e:
            print(f"LED 생성 오류: {e}")
            
    def update_basic_leds(self, values: Dict[str, Any]):
        """
        기본 LED 상태 업데이트
        
        Args:
            values: 센서 값 딕셔너리
        """
        try:
            # 값이 없는 경우 처리
            if not values:
                return
                
            # LED가 없는 경우 생성
            if not self.leds:
                numeric_sensors = [
                    sensor for sensor, value in values.items()
                    if isinstance(value, (int, float)) and 
                    not isinstance(value, bool)
                ]
                
                if numeric_sensors:
                    self.create_basic_leds(numeric_sensors)
            
            # LED 상태 업데이트
            for name, (canvas, led) in self.leds.items():
                if name in values:
                    value = values[name]
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        # 센서별 공식/권장 정상 범위에 따른 색상
                        color = 'gray'  # 기본값
                        # 온도
                        if name.lower() == 'temperature':
                            if value < 18:
                                color = 'blue'
                            elif 18 <= value <= 26:
                                color = 'green'
                            elif 26 < value <= 30:
                                color = 'yellow'
                            else:
                                color = 'red'
                        # 습도
                        elif name.lower() == 'humidity':
                            if value < 30:
                                color = 'blue'
                            elif 30 <= value < 40 or 60 < value <= 70:
                                color = 'yellow'
                            elif 40 <= value <= 60:
                                color = 'green'
                            else:
                                color = 'red'
                        # 압력(일반적으로 980~1050hPa가 정상)
                        elif name.lower() == 'pressure':
                            if 980 <= value <= 1050:
                                color = 'green'
                            elif 950 <= value < 980 or 1050 < value <= 1080:
                                color = 'yellow'
                            else:
                                color = 'red'
                        # CO2 (eco2)
                        elif name.lower() == 'eco2':
                            if 400 <= value <= 1000:
                                color = 'green'
                            elif 1000 < value <= 2000:
                                color = 'yellow'
                            else:
                                color = 'red'
                        # TVOC
                        elif name.lower() == 'tvoc':
                            if value <= 200:
                                color = 'green'
                            elif 200 < value <= 400:
                                color = 'yellow'
                            else:
                                color = 'red'
                        # 미세먼지(pm10, pm25, pm100)
                        elif 'pm10' in name.lower() or 'pm25' in name.lower() or 'pm100' in name.lower():
                            if value <= 15:
                                color = 'green'
                            elif 15 < value <= 35:
                                color = 'yellow'
                            else:
                                color = 'red'
                        # pt1, pt2 내부 미세먼지 값
                        elif name.startswith('pt1_') or name.startswith('pt2_'):
                            if 'pm10standard' in name.lower() or 'pm25standard' in name.lower() or 'pm100standard' in name.lower():
                                if value <= 15:
                                    color = 'green'
                                elif 15 < value <= 35:
                                    color = 'yellow'
                                else:
                                    color = 'red'
                            else:
                                color = 'green'  # 기타 파티클은 별도 기준 없음
                        # 기타 센서(임계값 미정)
                        else:
                            color = 'green'
                        # LED 색상 업데이트
                        canvas.itemconfig(led, fill=color)
                        # 레이블에 값 업데이트
                        unit = get_unit_for_sensor(name)
                        self.led_labels[name].config(text=f"{value:.1f} {unit}")
                    else:
                        # 숫자가 아닌 경우 회색으로 표시
                        canvas.itemconfig(led, fill='gray')
        except Exception as e:
            print(f"LED 업데이트 오류: {e}")
            
    def update_leds(self, values: Dict[str, Any]):
        """
        LED 상태 업데이트
        
        Args:
            values: 센서 값 딕셔너리
        """
        try:
            # 기본 LED 업데이트
            self.update_basic_leds(values)
            
            # 초기화되지 않은 경우 LED 생성
            if not self.initialized and values:
                self.create_basic_leds(list(values.keys()))
                self.initialized = True
                
        except Exception as e:
            print(f"LED 업데이트 오류: {e}")
            
    def set_status(self, is_active: bool):
        """
        LED 상태 설정
        
        Args:
            is_active: 활성화 여부
        """
        self.is_active = is_active
        
        # LED 상태 업데이트
        if is_active:
            self.status_canvas.itemconfig(self.status_led, fill='green')
        else:
            self.status_canvas.itemconfig(self.status_led, fill='red')

    def refresh_sensor_list(self, sensors: List[str]):
        """센서 목록 새로고침"""
        # 기존 위젯 제거
        for widget in self.led_grid.winfo_children():
            widget.destroy()
            
        if not sensors:
            self.placeholder = ttk.Label(
                self.led_grid,
                text="센서를 선택하세요",
                font=("AppleGothic", 10)
            )
            self.placeholder.pack(pady=10)
            return
            
        # 센서별 LED 표시 생성
        for i, sensor in enumerate(sensors):
            # 센서 이름 레이블
            sensor_label = ttk.Label(
                self.led_grid,
                text=f"{sensor}:",
                font=("AppleGothic", 9),
                anchor=tk.W
            )
            sensor_label.grid(row=i, column=0, padx=5, pady=2, sticky=tk.W)
            
            # LED 표시
            led_canvas = tk.Canvas(
                self.led_grid,
                width=self.digit_width,
                height=self.digit_height,
                bg=self.off_color,
                highlightthickness=0
            )
            led_canvas.grid(row=i, column=1, padx=5, pady=2)
            
            # LED 상태 저장
            self.leds[sensor] = led_canvas 