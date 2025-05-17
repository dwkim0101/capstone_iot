"""
메인 윈도우 모듈
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import csv
from datetime import datetime
import serial.tools.list_ports
from typing import Optional, Dict, Any
from ..core.data_collector import DataCollector
from ..core.data_processor import DataProcessor
from ..core.serial_handler import SerialHandler
from ..core.csv_handler import CsvHandler
from .graph_view import GraphView
from .led_display import LedDisplay
from .data_table import DataTable
from .stats_view import StatsView
from ..config.settings import (
    DEFAULT_BAUD_RATE, DEFAULT_PORT, APP_TITLE, FONT_FAMILY, SENSOR_UNITS, GRAPH_COLORS
)
import os
import sys
import platform
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
import numpy as np

# UI 컴포넌트
from duet_monitor.ui.port_selector import PortSelector
from duet_monitor.ui.data_control import DataControl
from duet_monitor.ui.sensor_control import SensorControl

# 윈도우 크기 상수 업데이트
WINDOW_TITLE = "DUET 모니터링 시스템"
WINDOW_SIZE = "2000x900"  # 가로 길이 증가
UPDATE_INTERVAL = 1000  # ms

class MainWindow:
    def __init__(self, root: tk.Tk, serial_handler: SerialHandler, 
                 csv_handler: CsvHandler, data_processor: DataProcessor):
        """
        메인 윈도우 초기화
        
        Args:
            root: 메인 윈도우
            serial_handler: 시리얼 통신 핸들러
            csv_handler: CSV 파일 핸들러
            data_processor: 데이터 처리기
        """
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)
        
        # 핸들러 저장
        self.serial_handler = serial_handler
        self.csv_handler = csv_handler
        self.data_processor = data_processor
        
        # 상태 변수
        self.is_lightweight_mode = False
        self.update_interval = UPDATE_INTERVAL  # ms
        self.last_update_time = 0
        self.update_count = 0
        
        # UI 초기화
        self.setup_ui()
        
        # 윈도우 종료 이벤트 핸들러
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 테스트 데이터 생성 (개발용)
        if "--test" in sys.argv:
            self.data_processor.generate_test_data(100)
            self.data_received_callback(self.data_processor.get_latest_values())
            
            # LED 디스플레이 테스트 데이터 전송
            if hasattr(self, 'led_display'):
                self.led_display.update_leds(self.data_processor.get_latest_values())
                
        # 최초 UI 업데이트 스케줄링
        self.schedule_update()
        
    def setup_ui(self):
        """UI 초기화"""
        # 스타일 설정
        self.setup_style()
        
        # 메인 프레임
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 하단 프레임 (상태 표시줄)
        self.bottom_frame = ttk.Frame(self.main_frame, height=30)
        self.bottom_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)
        
        # 성능 모니터링 레이블
        self.perf_label = ttk.Label(self.bottom_frame, text="업데이트 간격: 준비 중")
        self.perf_label.pack(side=tk.LEFT, padx=5)
        
        # 모드 전환 버튼
        self.mode_toggle_button = ttk.Button(
            self.bottom_frame, 
            text="경량 모드로 전환", 
            command=self.toggle_mode,
            width=20
        )
        self.mode_toggle_button.pack(side=tk.RIGHT, padx=10)
        
        # 상태 레이블
        self.status_label = ttk.Label(self.bottom_frame, text="준비")
        self.status_label.pack(side=tk.RIGHT, padx=5)
        
        # 콘텐츠 프레임 (상단+중단 통합)
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 좌측 제어 패널 영역 - 하나의 LabelFrame으로 통합
        self.control_frame = ttk.LabelFrame(self.content_frame, text="제어 패널", width=380)
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        self.control_frame.pack_propagate(False)  # 너비 고정
        
        # 1. 포트 선택기
        self.port_selector = PortSelector(self.control_frame, self.serial_handler)
        self.port_selector.pack(fill=tk.X, padx=10, pady=(15, 5))
        
        # 구분선 추가
        separator1 = ttk.Separator(self.control_frame, orient='horizontal')
        separator1.pack(fill=tk.X, padx=10, pady=10)
        
        # 2. 센서 제어
        self.sensor_control = SensorControl(self.control_frame, self.data_processor)
        self.sensor_control.pack(fill=tk.X, padx=10, pady=5)
        
        # 구분선 추가
        separator2 = ttk.Separator(self.control_frame, orient='horizontal')
        separator2.pack(fill=tk.X, padx=10, pady=10)
        
        # 3. 데이터 제어
        self.data_control = DataControl(
            self.control_frame,
            self.serial_handler,
            self.csv_handler,
            self.data_processor,
            self.start_collection,
            self.stop_collection
        )
        self.data_control.pack(fill=tk.X, padx=10, pady=5)
        
        # 중앙 및 우측 콘텐츠 프레임
        self.right_content_frame = ttk.Frame(self.content_frame)
        self.right_content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 중앙 영역 (그래프 + 테이블)
        self.middle_frame = ttk.Frame(self.right_content_frame, width=800)  # 너비 감소
        self.middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.middle_frame.pack_propagate(False)  # 너비 고정
        
        # 그래프 영역
        self.graph_frame = ttk.LabelFrame(self.middle_frame, text="센서 데이터 그래프")
        self.graph_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 그래프 모드 전환 버튼
        self.graph_mode_frame = ttk.Frame(self.graph_frame)
        self.graph_mode_frame.pack(fill=tk.X, padx=5, pady=2)
        
        self.graph_mode_button = ttk.Button(
            self.graph_mode_frame,
            text="다중 센서 그래프 켜기",
            command=self.toggle_multi_sensor_graph,
            width=20
        )
        self.graph_mode_button.pack(side=tk.RIGHT, padx=5, pady=2)
        
        # 다중 센서 선택 프레임
        self.multi_sensor_frame = ttk.LabelFrame(self.graph_frame, text="다중 센서 선택")
        
        # 스크롤 가능한 센서 선택 영역
        self.multi_sensor_canvas = tk.Canvas(self.multi_sensor_frame, height=100)
        self.multi_sensor_scrollbar = ttk.Scrollbar(self.multi_sensor_frame, orient=tk.VERTICAL, command=self.multi_sensor_canvas.yview)
        self.multi_sensor_scrollable_frame = ttk.Frame(self.multi_sensor_canvas)
        
        self.multi_sensor_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.multi_sensor_canvas.configure(
                scrollregion=self.multi_sensor_canvas.bbox("all")
            )
        )
        
        self.multi_sensor_canvas.create_window((0, 0), window=self.multi_sensor_scrollable_frame, anchor="nw")
        self.multi_sensor_canvas.configure(yscrollcommand=self.multi_sensor_scrollbar.set)
        
        self.multi_sensor_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.multi_sensor_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,5), pady=5)
        
        # 선택된 센서 저장
        self.selected_graph_sensors = []
        self.sensor_checkboxes = {}
        self.sensor_vars = {}
        
        # 그래프 캔버스 프레임
        self.graph_canvas_frame = ttk.Frame(self.graph_frame)
        self.graph_canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        
        # 그래프 생성
        self.fig = Figure(figsize=(5, 4))  # 그래프 크기 감소
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_canvas_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 그래프 설정
        self.ax.set_title("센서 데이터")
        self.ax.set_xlabel("시간")
        self.ax.set_ylabel("값")
        self.ax.grid(True)
        
        # 데이터 테이블 (그래프 아래)
        self.table_frame = ttk.LabelFrame(self.middle_frame, text="데이터 테이블")
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 스크롤바 추가
        table_scroll = ttk.Scrollbar(self.table_frame, orient=tk.HORIZONTAL)
        table_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.data_table = DataTable(self.table_frame, xscrollcommand=table_scroll.set)
        self.data_table.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        table_scroll.config(command=self.data_table.xview)
        
        # 우측 영역 (LED 디스플레이 + 통계)
        self.side_frame = ttk.Frame(self.right_content_frame, width=900)  # 너비 증가
        self.side_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)
        self.side_frame.pack_propagate(False)  # 너비 고정
        
        # LED 디스플레이와 통계를 담을 수평 프레임
        self.horizontal_frame = ttk.Frame(self.side_frame)
        self.horizontal_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # LED 디스플레이 (왼쪽)
        self.led_frame = ttk.LabelFrame(self.horizontal_frame, text="센서 상태", width=300)  # 너비 유지
        self.led_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 2), pady=5)
        self.led_frame.pack_propagate(False)  # 크기 고정
        
        self.led_display = LedDisplay(self.led_frame)
        self.led_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 통계 뷰 (오른쪽)
        self.stats_frame = ttk.LabelFrame(self.horizontal_frame, text="통계 정보", width=400)  # 너비 증가
        self.stats_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(2, 0), pady=5)
        self.stats_frame.pack_propagate(False)  # 크기 고정
        
        self.stats_view = StatsView(self.stats_frame)
        self.stats_view.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def toggle_mode(self):
        """모드 전환 버튼 클릭 핸들러"""
        # 현재 모드 반전
        new_mode = not self.is_lightweight_mode
        
        # 모드 설정
        self.set_lightweight_mode(new_mode)
        
        # 버튼 텍스트 업데이트
        if new_mode:
            self.mode_toggle_button.config(text="전체 모드로 전환")
        else:
            self.mode_toggle_button.config(text="경량 모드로 전환")
        
    def set_lightweight_mode(self, enabled: bool):
        """경량 모드 설정"""
        self.is_lightweight_mode = enabled
        # 상태 표시 업데이트
        status_message_type = getattr(self, 'status_message_type', {"current": None})
        if enabled:
            # 경량 모드로 전환
            # 데이터 테이블 영역 숨김
            if hasattr(self, 'data_table'):
                self.data_table.master.pack_forget()  # LabelFrame 전체를 숨김
                
            # 통계 뷰 영역 숨김
            if hasattr(self, 'stats_view'):
                self.stats_view.master.pack_forget()  # LabelFrame 전체를 숨김
            
            # LED 디스플레이 숨김
            if hasattr(self, 'led_display'):
                self.led_display.master.pack_forget()  # LED 디스플레이 프레임 전체를 숨김
            
            # 그래프 영역 숨김
            if hasattr(self, 'fig'):
                self.canvas.get_tk_widget().master.pack_forget()  # 그래프 프레임 숨김
            
            # 중앙 및 우측 콘텐츠 프레임 숨김
            if hasattr(self, 'right_content_frame'):
                self.right_content_frame.pack_forget()
            
            # 업데이트 간격 증가
            self.update_interval = 5000  # 5초
            
            # 데이터 프로세서 최적화
            if hasattr(self, 'data_processor'):
                self.data_processor.set_max_rows(500)  # 메모리 사용량 제한
            
            # 상태 표시 업데이트
            if status_message_type.get("current") != "error":
                print("[DEBUG][set_lightweight_mode] 상태바: ⚡ 경량 모드 활성화됨")
                self.status_label.config(text="⚡ 경량 모드 활성화됨", foreground="blue")
            
            # 데이터 컨트롤 경량 모드 설정
            if hasattr(self, 'data_control') and hasattr(self.data_control, 'lightweight_var'):
                self.data_control.lightweight_var.set(True)
            
            # 창 타이틀 업데이트
            self.root.title(f"{WINDOW_TITLE} [경량 모드]")
            
            # 윈도우 크기 자동 조정
            self.root.update_idletasks()
            
            # 제어 패널의 크기 가져오기
            control_width = self.control_frame.winfo_reqwidth()
            control_height = self.control_frame.winfo_reqheight()
            
            # 메인 프레임의 패딩 고려
            main_padding = 20  # 상하 패딩 10픽셀씩
            bottom_frame_height = 40  # 하단 프레임 높이
            
            # 전체 창 높이 계산 (원래 높이 유지)
            window_height = 900  # 원래 창 높이 유지
            
            # 창 크기 설정
            self.root.geometry(f"{control_width + 40}x{window_height}")  # 여백 20픽셀씩 추가
            
            # 제어 패널이 전체 높이를 채우도록 설정
            self.control_frame.pack_propagate(False)
            self.control_frame.configure(height=window_height - main_padding - bottom_frame_height)
        else:
            # 전체 모드로 전환
            # 중앙 및 우측 콘텐츠 프레임 표시
            if hasattr(self, 'right_content_frame'):
                self.right_content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # 중앙 영역 (그래프 + 테이블)
            if hasattr(self, 'middle_frame'):
                self.middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # 그래프 영역 표시
            if hasattr(self, 'fig'):
                self.canvas.get_tk_widget().master.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # 데이터 테이블 표시
            if hasattr(self, 'data_table'):
                self.data_table.master.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # 우측 영역 (LED 디스플레이 + 통계)
            if hasattr(self, 'side_frame'):
                self.side_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # LED 디스플레이와 통계를 담을 수평 프레임
            if hasattr(self, 'horizontal_frame'):
                self.horizontal_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # LED 디스플레이 표시
            if hasattr(self, 'led_display'):
                self.led_display.master.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 2), pady=5)
            
            # 통계 뷰 표시
            if hasattr(self, 'stats_view'):
                self.stats_view.master.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(2, 0), pady=5)
            
            # 업데이트 간격 복원
            self.update_interval = UPDATE_INTERVAL  # 1초
            
            # 데이터 프로세서 복원
            if hasattr(self, 'data_processor'):
                self.data_processor.set_max_rows(1000)
            
            # 상태 표시 업데이트
            if status_message_type.get("current") != "error":
                print("[DEBUG][set_lightweight_mode] 상태바: 준비")
                self.status_label.config(text="준비", foreground="black")
            
            # 데이터 컨트롤 일반 모드 설정
            if hasattr(self, 'data_control') and hasattr(self.data_control, 'lightweight_var'):
                self.data_control.lightweight_var.set(False)
                
            # 창 타이틀 복원
            self.root.title(WINDOW_TITLE)
            
            # 윈도우 크기 복원
            self.root.geometry(WINDOW_SIZE)
            
            # UI 업데이트 및 레이아웃 재조정
            self.root.update_idletasks()
            
            # 그래프 레이아웃 조정
            if hasattr(self, 'fig'):
                self.fig.tight_layout()
                self.canvas.draw()
            
            # 데이터 테이블 업데이트
            if hasattr(self, 'data_table'):
                df = self.data_processor.get_dataframe()
                if df is not None and not df.empty:
                    self.data_table.update_table(df)
            
            # 통계 정보 업데이트
            if hasattr(self, 'stats_view'):
                latest_values = self.data_processor.get_latest_values()
                self.stats_view.update_stats(latest_values)
            
            # LED 디스플레이 업데이트
            if hasattr(self, 'led_display'):
                latest_values = self.data_processor.get_latest_values()
                self.led_display.update_leds(latest_values)
            
            # 센서 제어 패널 업데이트
            if hasattr(self, 'sensor_control'):
                latest_values = self.data_processor.get_latest_values()
                self.sensor_control.update_sensor_list(latest_values)
                self.sensor_control.update_display(latest_values)
        
        # 업데이트 타이머 재설정
        self.schedule_update()
        
    def set_update_interval(self, ms: int):
        """업데이트 간격 설정"""
        self.update_interval = ms
        self.schedule_update()
        
    def schedule_update(self):
        """업데이트 타이머 예약"""
        if self.update_interval > 0:
            self.root.after(self.update_interval, self.update_ui)
            
    def update_ui(self):
        """UI 업데이트"""
        try:
            # 성능 모니터링
            current_time = time.time()
            if self.last_update_time > 0:
                interval = current_time - self.last_update_time
                self.update_count += 1
                avg_interval = interval / self.update_count
                
                # 모드에 따른 성능 정보 표시
                if self.is_lightweight_mode:
                    self.perf_label.config(text=f"경량 모드 | 평균 업데이트 간격: {avg_interval:.2f}초")
                else:
                    self.perf_label.config(text=f"전체 모드 | 평균 업데이트 간격: {avg_interval:.2f}초")
                    
            self.last_update_time = current_time
            
            # 데이터프레임 가져오기
            df = self.data_processor.get_dataframe()
            
            if df is not None and not df.empty:
                # 그래프 업데이트 (모든 모드에서 공통)
                self.update_graph()
                
                # LED 디스플레이 업데이트 (모든 모드에서 공통)
                if hasattr(self, 'led_display'):
                    latest_values = self.data_processor.get_latest_values()
                    self.led_display.update_leds(latest_values)
                    
                    # 센서 제어 패널의 7세그먼트 디스플레이 업데이트
                    if hasattr(self, 'sensor_control'):
                        self.sensor_control.update_sensor_list(latest_values)
                        self.sensor_control.update_display(latest_values)
                
                # 경량 모드가 아닌 경우에만 추가 UI 요소 업데이트
                if not self.is_lightweight_mode:
                    # 테이블 업데이트
                    if hasattr(self, 'data_table'):
                        self.data_table.update_table(df)
                    
                    # 통계 업데이트
                    if hasattr(self, 'stats_view'):
                        latest_values = self.data_processor.get_latest_values()
                        self.stats_view.update_stats(latest_values)
            
            # 다음 업데이트 예약
            self.schedule_update()
            
        except Exception as e:
            print(f"UI 업데이트 중 오류: {e}")
            import traceback
            print(traceback.format_exc())
            
    def update_graph(self):
        """그래프 업데이트"""
        try:
            # 선택된 센서가 없으면 그래프 초기화
            if not hasattr(self, 'data_processor') or not hasattr(self, 'sensor_control'):
                return
            
            # 데이터 가져오기
            df = self.data_processor.get_dataframe()
            
            if df is None or df.empty:
                self.ax.clear()
                self.ax.set_title("데이터 없음")
                self.ax.grid(True)
                self.canvas.draw()
                return
            
            # 그래프 초기화
            self.ax.clear()
            
            # 다중 센서 표시
            if hasattr(self, 'show_multiple_sensors') and self.show_multiple_sensors:
                # 선택된 센서 가져오기
                selected_sensors = self.get_selected_graph_sensors()
                
                if not selected_sensors:
                    # 선택된 센서가 없으면 안내 메시지 표시
                    self.ax.text(0.5, 0.5, '표시할 센서를 선택하세요', 
                            horizontalalignment='center', verticalalignment='center',
                            transform=self.ax.transAxes)
                else:
                    # 각 센서별로 그래프 추가
                    for column in selected_sensors:
                        if column in df.columns:
                            # 최근 50개 데이터만 표시
                            recent_data = df[column].iloc[-50:]
                            self.ax.plot(range(len(recent_data)), recent_data, label=column)
                    
                    # 범례 추가
                    self.ax.legend(loc='upper right', fontsize='small')
            else:
                # 단일 센서 표시 (기존 방식)
                selected_sensor = self.sensor_control.get_selected_sensor()
                
                if selected_sensor and selected_sensor in df.columns:
                    # 최근 50개 데이터만 표시
                    recent_data = df[selected_sensor].iloc[-50:]
                    self.ax.plot(range(len(recent_data)), recent_data)
                    
                    # 센서 이름과 단위 표시
                    from ..config.settings import SENSOR_UNITS
                    unit = SENSOR_UNITS.get(selected_sensor, "")
                    title = f"{selected_sensor} {unit}"
                    self.ax.set_title(title)
                else:
                    self.ax.set_title("센서를 선택하세요")
            
            # 그래프 공통 설정
            self.ax.grid(True)
            self.ax.set_xlabel("시간")
            self.ax.set_ylabel("값")
            
            # 그래프 그리기
            self.fig.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            print(f"그래프 업데이트 오류: {e}")
            import traceback
            traceback.print_exc()
            
    def toggle_multi_sensor_graph(self):
        """다중 센서 그래프 토글"""
        if not hasattr(self, 'show_multiple_sensors'):
            self.show_multiple_sensors = True
        else:
            self.show_multiple_sensors = not self.show_multiple_sensors
            
        # 버튼 텍스트 업데이트
        if self.show_multiple_sensors:
            self.graph_mode_button.config(text="단일 센서 그래프로 전환")
            # 다중 센서 선택 프레임 표시
            self.multi_sensor_frame.pack(fill=tk.X, padx=5, pady=5, before=self.graph_canvas_frame)
            # 센서 체크박스 업데이트
            self.update_sensor_checkboxes()
        else:
            self.graph_mode_button.config(text="다중 센서 그래프로 전환")
            # 다중 센서 선택 프레임 숨김
            self.multi_sensor_frame.pack_forget()
            
        # 그래프 업데이트
        self.update_graph()
        
    def update_sensor_checkboxes(self):
        """센서 체크박스 업데이트"""
        # 기존 체크박스 제거
        for widget in self.multi_sensor_scrollable_frame.winfo_children():
            widget.destroy()
            
        self.sensor_vars = {}
        self.sensor_checkboxes = {}
        
        # 데이터프레임 가져오기
        df = self.data_processor.get_dataframe()
        if df is None or df.empty:
            return
            
        # 숫자형 센서 컬럼 찾기
        numeric_columns = [
            col for col in df.columns 
            if df[col].dtype in ['int64', 'float64'] and not df[col].apply(lambda x: isinstance(x, bool)).any()
        ]
        
        # 센서별 체크박스 생성
        for i, column in enumerate(numeric_columns):
            var = tk.BooleanVar(value=i < 5)  # 처음 5개 센서는 기본 선택
            
            checkbox = ttk.Checkbutton(
                self.multi_sensor_scrollable_frame,
                text=column,
                variable=var,
                command=self.update_graph
            )
            checkbox.grid(row=i//2, column=i%2, sticky=tk.W, padx=5, pady=2)
            
            self.sensor_vars[column] = var
            self.sensor_checkboxes[column] = checkbox
            
    def get_selected_graph_sensors(self):
        """선택된 그래프 센서 목록 반환"""
        if not hasattr(self, 'sensor_vars') or not self.sensor_vars:
            return []
            
        return [sensor for sensor, var in self.sensor_vars.items() if var.get()]
        
    def manual_update(self):
        """수동 UI 업데이트"""
        self.update_ui()
        
    def start_collection(self):
        """데이터 수집 시작"""
        # 성능 모니터링 초기화
        self.last_update_time = time.time()
        self.update_count = 0
        status_message_type = getattr(self, 'status_message_type', {"current": None})
        if status_message_type.get("current") != "error":
            if self.is_lightweight_mode:
                print("[DEBUG][start_collection] 상태바: 데이터 수집 중... (경량 모드)")
                self.status_label.config(text="데이터 수집 중... (경량 모드)", foreground="blue")
            else:
                print("[DEBUG][start_collection] 상태바: 데이터 수집 중...")
                self.status_label.config(text="데이터 수집 중...", foreground="green")
        # LED 상태 업데이트 (모든 모드에서 공통)
        if hasattr(self, 'led_display'):
            self.led_display.set_status(True)
        
    def stop_collection(self):
        """데이터 수집 중지"""
        status_message_type = getattr(self, 'status_message_type', {"current": None})
        if status_message_type.get("current") != "error":
            if self.is_lightweight_mode:
                print("[DEBUG][stop_collection] 상태바: 준비 (경량 모드)")
                self.status_label.config(text="준비 (경량 모드)", foreground="blue")
            else:
                print("[DEBUG][stop_collection] 상태바: 준비")
                self.status_label.config(text="준비", foreground="black")
        # LED 상태 업데이트 (모든 모드에서 공통)
        if hasattr(self, 'led_display'):
            self.led_display.set_status(False)
        
    def data_received_callback(self, data: Dict[str, Any]):
        """
        시리얼 데이터 수신 콜백
        
        Args:
            data: 수신된 데이터
        """
        # 데이터 처리
        self.data_processor.update_dataframe(data)
        
        # CSV 파일 업데이트 (데이터 제어에서 처리)
        if hasattr(self, 'data_control'):
            self.data_control.append_csv_data(data)
            
        # 경량 모드가 아니고 수동 업데이트도 아니면 바로 UI 업데이트
        if not self.is_lightweight_mode and self.update_interval > 0:
            # UI 업데이트 필요 없음 - 자동으로 처리됨
            pass
        
    def on_closing(self):
        """윈도우 종료 이벤트 핸들러"""
        # 시리얼 연결 종료
        if self.serial_handler:
            self.serial_handler.close()
            
        # 종료
        self.root.destroy()
        
    def run(self):
        """애플리케이션 실행"""
        self.root.mainloop()

    def setup_style(self):
        """Tkinter 스타일 설정"""
        style = ttk.Style()
        
        # 시스템 테마 확인
        system = platform.system()
        
        # 플랫폼별 테마 설정
        if system == "Windows":
            style.theme_use("vista")
        elif system == "Darwin":  # macOS
            style.theme_use("aqua")
        else:  # Linux 등
            style.theme_use("clam")
            
        # 글꼴 설정
        default_font = (FONT_FAMILY, 10)
        
        # 위젯별 스타일 설정
        style.configure("TLabel", font=default_font)
        style.configure("TButton", font=default_font)
        style.configure("TCheckbutton", font=default_font)
        style.configure("TRadiobutton", font=default_font)
        style.configure("TEntry", font=default_font)
        style.configure("TCombobox", font=default_font)
        
        # 프레임 테두리 설정
        style.configure("TLabelframe", font=default_font)
        style.configure("TLabelframe.Label", font=(FONT_FAMILY, 10, "bold"))
        
        # 패널 스타일
        style.configure("Panel.TFrame", relief=tk.RIDGE, borderwidth=2)
        
        # 데이터 수집 버튼 스타일
        style.configure("Start.TButton", foreground="white", background="green", font=(FONT_FAMILY, 12, "bold"))
        style.configure("Stop.TButton", foreground="white", background="red", font=(FONT_FAMILY, 12, "bold"))
        
        # LED 디스플레이 스타일
        style.configure("LED.TLabel", font=(FONT_FAMILY, 14, "bold"), padding=5)
        style.configure("LED.On.TLabel", foreground="green")
        style.configure("LED.Off.TLabel", foreground="red") 