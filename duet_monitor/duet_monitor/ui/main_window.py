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
WINDOW_SIZE = "1600x900"  # 가로 길이 증가
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
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 하단 프레임 (상태 표시줄)
        self.bottom_frame = ttk.Frame(main_frame, height=30)
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
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 좌측 제어 패널 영역 - 하나의 LabelFrame으로 통합
        self.control_frame = ttk.LabelFrame(content_frame, text="제어 패널", width=380)
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
        self.right_content_frame = ttk.Frame(content_frame)
        self.right_content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 중앙 영역 (그래프 + 테이블)
        middle_frame = ttk.Frame(self.right_content_frame, width=400)  # 너비 감소
        middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        middle_frame.pack_propagate(False)  # 너비 고정
        
        # 그래프 영역
        graph_frame = ttk.LabelFrame(middle_frame, text="센서 데이터 그래프")
        graph_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 그래프 생성
        self.fig = Figure(figsize=(5, 4))  # 그래프 크기 감소
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 그래프 설정
        self.ax.set_title("센서 데이터")
        self.ax.set_xlabel("시간")
        self.ax.set_ylabel("값")
        self.ax.grid(True)
        
        # 데이터 테이블 (그래프 아래)
        table_frame = ttk.LabelFrame(middle_frame, text="데이터 테이블")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 스크롤바 추가
        table_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        table_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.data_table = DataTable(table_frame, xscrollcommand=table_scroll.set)
        self.data_table.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        table_scroll.config(command=self.data_table.xview)
        
        # 우측 영역 (LED 디스플레이 + 통계)
        side_frame = ttk.Frame(self.right_content_frame, width=700)  # 너비 증가
        side_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)
        side_frame.pack_propagate(False)  # 너비 고정
        
        # LED 디스플레이와 통계를 담을 수평 프레임
        horizontal_frame = ttk.Frame(side_frame)
        horizontal_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # LED 디스플레이 (왼쪽)
        led_frame = ttk.LabelFrame(horizontal_frame, text="센서 상태", width=400)  # 너비 증가
        led_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 2), pady=5)
        led_frame.pack_propagate(False)  # 크기 고정
        
        self.led_display = LedDisplay(led_frame)
        self.led_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 통계 뷰 (오른쪽)
        stats_frame = ttk.LabelFrame(horizontal_frame, text="통계 정보")
        stats_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(2, 0), pady=5)
        
        self.stats_view = StatsView(stats_frame)
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
        
        if enabled:
            # 경량 모드로 전환
            # 중앙 및 우측 콘텐츠 프레임 숨김
            if hasattr(self, 'right_content_frame'):
                self.right_content_frame.pack_forget()
            
            # 업데이트 간격 증가
            self.update_interval = 5000  # 5초
            
            # 데이터 프로세서 최적화
            if hasattr(self, 'data_processor'):
                self.data_processor.set_max_rows(500)  # 메모리 사용량 제한
            
            # 상태 표시 업데이트
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
            
            # 업데이트 간격 복원
            self.update_interval = UPDATE_INTERVAL  # 1초
            
            # 데이터 프로세서 복원
            if hasattr(self, 'data_processor'):
                self.data_processor.set_max_rows(1000)
            
            # 상태 표시 업데이트
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
            if hasattr(self, 'fig'):
                self.fig.tight_layout()
                self.canvas.draw()
            
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
                self.update_graph(df)
                
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
            
    def update_graph(self, df: pd.DataFrame):
        """그래프 업데이트"""
        try:
            # 그래프 초기화
            self.ax.clear()
            
            # 선택된 센서 가져오기
            selected_sensor = self.sensor_control.get_selected_sensor()
            
            if selected_sensor and selected_sensor in df.columns:
                # 데이터 타입 확인
                if df[selected_sensor].dtype == 'object':
                    # 딕셔너리 타입인 경우 특별 처리
                    is_dict_type = df[selected_sensor].apply(lambda x: isinstance(x, dict)).any()
                    
                    if is_dict_type:
                        # PT1 또는 PT2와 같은 딕셔너리 필드인 경우
                        # 각 딕셔너리의 첫 번째 키에 해당하는 값 시각화 (예: pm10_standard)
                        if selected_sensor in ['pt1', 'pt2']:
                            # 특정 파티클 매트릭을 선택 (pm25_standard가 가장 중요)
                            metric = "pm25_standard"
                            y_data = df[selected_sensor].apply(
                                lambda x: float(x.get(metric, 0)) if isinstance(x, dict) else 0
                            )
                            plot_title = f"{selected_sensor} - {metric}"
                            
                            # 같은 크기의 인덱스 배열 생성 (0부터 시작)
                            x_data = np.arange(len(y_data))
                            
                            # 플롯
                            color = GRAPH_COLORS.get(selected_sensor, 'blue')
                            self.ax.plot(x_data, y_data, color=color, label=plot_title, linewidth=1.5)
                            
                            # 레이블 설정
                            unit = SENSOR_UNITS.get(selected_sensor, '')
                            if unit:
                                self.ax.set_ylabel(f"{plot_title} ({unit})")
                            else:
                                self.ax.set_ylabel(plot_title)
                        else:
                            # 일반 딕셔너리 필드인 경우, 첫 번째 키의 값을 사용
                            first_dict = df[selected_sensor].iloc[0]
                            if isinstance(first_dict, dict) and len(first_dict) > 0:
                                first_key = list(first_dict.keys())[0]
                                y_data = df[selected_sensor].apply(
                                    lambda x: float(x.get(first_key, 0)) if isinstance(x, dict) else 0
                                )
                                
                                # 같은 크기의 인덱스 배열 생성 (0부터 시작)
                                x_data = np.arange(len(y_data))
                                
                                # 플롯
                                color = GRAPH_COLORS.get(selected_sensor, 'blue')
                                self.ax.plot(x_data, y_data, color=color, label=f"{selected_sensor}.{first_key}", linewidth=1.5)
                                
                                # 레이블 설정
                                self.ax.set_ylabel(f"{selected_sensor}.{first_key}")
                            else:
                                # 딕셔너리가 아니거나 비어있는 경우 오류 메시지 표시
                                self.ax.text(0.5, 0.5, f"선택된 센서({selected_sensor})에 대한 데이터가 올바르지 않습니다",
                                          horizontalalignment='center', verticalalignment='center',
                                          transform=self.ax.transAxes)
                    else:
                        # 일반 수치 데이터로 변환 가능한지 확인
                        try:
                            y_data = df[selected_sensor].astype(float)
                            
                            # 같은 크기의 인덱스 배열 생성 (0부터 시작)
                            x_data = np.arange(len(y_data))
                            
                            # 플롯
                            color = GRAPH_COLORS.get(selected_sensor, 'blue')
                            self.ax.plot(x_data, y_data, color=color, label=selected_sensor, linewidth=1.5)
                            
                            # 레이블 설정
                            unit = SENSOR_UNITS.get(selected_sensor, '')
                            if unit:
                                self.ax.set_ylabel(f"{selected_sensor} ({unit})")
                            else:
                                self.ax.set_ylabel(selected_sensor)
                        except (ValueError, TypeError):
                            # 변환할 수 없는 경우 메시지 표시
                            self.ax.text(0.5, 0.5, f"선택된 센서({selected_sensor})의 데이터를 그래프로 표시할 수 없습니다",
                                      horizontalalignment='center', verticalalignment='center',
                                      transform=self.ax.transAxes)
                else:
                    # 일반 숫자 타입인 경우 직접 플롯
                    # 같은 크기의 인덱스 배열 생성 (0부터 시작)
                    x_data = np.arange(len(df[selected_sensor]))
                    
                    # 플롯
                    color = GRAPH_COLORS.get(selected_sensor, 'blue')
                    self.ax.plot(x_data, df[selected_sensor], color=color, label=selected_sensor, linewidth=1.5)
                    
                    # 레이블 설정
                    unit = SENSOR_UNITS.get(selected_sensor, '')
                    if unit:
                        self.ax.set_ylabel(f"{selected_sensor} ({unit})")
                    else:
                        self.ax.set_ylabel(selected_sensor)
            else:
                # 선택된 센서가 없거나 데이터프레임에 없는 경우
                self.ax.text(0.5, 0.5, "센서를 선택해주세요",
                          horizontalalignment='center', verticalalignment='center',
                          transform=self.ax.transAxes)
                self.ax.set_ylabel("값")
                
            # 그래프 설정
            self.ax.set_title("센서 데이터")
            self.ax.set_xlabel("샘플 인덱스")
            self.ax.grid(True, linestyle='--', alpha=0.7)
            
            # 범례 추가
            self.ax.legend(loc='upper right')
            
            # x축 틱 조정 (데이터가 많은 경우 일부만 표시)
            if len(df) > 10:
                tick_step = max(1, len(df) // 10)  # 최대 10개의 틱 표시
                self.ax.set_xticks(np.arange(0, len(df), tick_step))
            
            # 레이아웃 조정
            try:
                self.fig.tight_layout()
            except Exception as layout_error:
                print(f"레이아웃 조정 중 오류: {layout_error}")
            
            # 캔버스 업데이트
            self.canvas.draw()
            
        except Exception as e:
            print(f"그래프 업데이트 중 오류: {e}")
            import traceback
            print(traceback.format_exc())
            
    def manual_update(self):
        """수동 UI 업데이트"""
        self.update_ui()
        
    def start_collection(self):
        """데이터 수집 시작"""
        # 성능 모니터링 초기화
        self.last_update_time = time.time()
        self.update_count = 0
        
        # 상태 업데이트
        if self.is_lightweight_mode:
            self.status_label.config(text="데이터 수집 중... (경량 모드)", foreground="blue")
        else:
            self.status_label.config(text="데이터 수집 중...", foreground="green")
        
        # LED 상태 업데이트 (모든 모드에서 공통)
        if hasattr(self, 'led_display'):
            self.led_display.set_status(True)
        
    def stop_collection(self):
        """데이터 수집 중지"""
        # 상태 업데이트
        if self.is_lightweight_mode:
            self.status_label.config(text="준비 (경량 모드)", foreground="blue")
        else:
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