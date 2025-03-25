"""
LED 디스플레이 모듈
"""
import tkinter as tk
from tkinter import ttk
from typing import Dict, Any
from ..config.settings import LED_COLORS, LED_SIZE

class LEDDisplay(ttk.Frame):
    def __init__(self, parent: tk.Tk):
        """
        LED 디스플레이 초기화
        
        Args:
            parent: 부모 위젯
        """
        super().__init__(parent)
        self.parent = parent
        self.leds: Dict[str, tk.Canvas] = {}
        self.setup_ui()
        
    def setup_ui(self):
        """UI 초기화"""
        # LED 프레임
        self.led_frame = ttk.Frame(self)
        self.led_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # LED 캔버스 생성
        for i, (name, color) in enumerate(LED_COLORS.items()):
            # LED 레이블
            ttk.Label(self.led_frame, text=name).grid(row=i, column=0, padx=5, pady=2)
            
            # LED 캔버스
            canvas = tk.Canvas(self.led_frame, width=LED_SIZE, height=LED_SIZE, bg='white')
            canvas.grid(row=i, column=1, padx=5, pady=2)
            
            # LED 원 그리기
            canvas.create_oval(2, 2, LED_SIZE-2, LED_SIZE-2, fill='gray')
            
            self.leds[name] = canvas
            
    def update_leds(self, values: Dict[str, Any]):
        """
        LED 상태 업데이트
        
        Args:
            values: 센서 값 딕셔너리
        """
        try:
            for name, canvas in self.leds.items():
                if name in values:
                    value = values[name]
                    if isinstance(value, (int, float)):
                        # 임계값에 따른 색상 설정
                        if value > 80:
                            color = 'red'
                        elif value > 60:
                            color = 'yellow'
                        else:
                            color = 'green'
                    else:
                        color = 'gray'
                        
                    # LED 색상 업데이트
                    canvas.itemconfig(1, fill=color)
                    
        except Exception as e:
            print(f"LED 업데이트 오류: {e}")
            
    def clear(self):
        """LED 초기화"""
        for canvas in self.leds.values():
            canvas.itemconfig(1, fill='gray') 