"""
그래프 뷰 모듈
"""
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
import matplotlib.dates as mdates
import matplotlib as mpl
from typing import List, Dict, Any, Optional
from duet_monitor.config.settings import MAX_DATA_POINTS, FONT_FAMILY, GRAPH_COLORS, SENSOR_UNITS

# 한글 폰트 설정 적용
mpl.rcParams['font.family'] = FONT_FAMILY
mpl.rcParams['axes.unicode_minus'] = False

class GraphView(ttk.LabelFrame):
    def __init__(self, parent: tk.Widget):
        """
        그래프 뷰 초기화
        
        Args:
            parent: 부모 위젯
        """
        super().__init__(parent, text="센서 그래프")
        self.parent = parent
        
        # 그래프 설정
        self.fig = None
        self.ax = None
        self.canvas = None
        self.selected_sensor = None
        self.separate_mode = False
        self.separate_sensors = []
        
        # UI 초기화
        self.setup_ui()
        
    def setup_ui(self):
        """UI 초기화"""
        # 메인 프레임
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 그래프 컨트롤 프레임
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 센서 선택 콤보박스
        ttk.Label(control_frame, text="센서:").pack(side=tk.LEFT, padx=5)
        self.sensor_var = tk.StringVar()
        self.sensor_combo = ttk.Combobox(
            control_frame,
            textvariable=self.sensor_var,
            values=[],
            state="readonly",
            width=15
        )
        self.sensor_combo.pack(side=tk.LEFT, padx=5)
        self.sensor_combo.bind("<<ComboboxSelected>>", self.on_sensor_selected)
        
        # 분리 모드 체크박스
        self.separate_var = tk.BooleanVar(value=False)
        self.separate_check = ttk.Checkbutton(
            control_frame,
            text="다중 센서 표시",
            variable=self.separate_var,
            command=self.toggle_separate_mode
        )
        self.separate_check.pack(side=tk.LEFT, padx=15)
        
        # 그래프 프레임
        self.graph_frame = ttk.Frame(main_frame)
        self.graph_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 그래프 초기화
        self.create_figure()
        
    def create_figure(self):
        """그래프 생성"""
        # Figure 생성
        self.fig = Figure(figsize=(8, 4), dpi=100)
        self.fig.set_facecolor('white')
        
        # Axes 생성
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('white')
        self.ax.grid(True, linestyle='--', alpha=0.7)
        
        # Canvas 생성
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 그래프 기본 설정
        self.ax.set_title("센서 데이터", pad=20)
        self.ax.set_xlabel("시간")
        self.ax.set_ylabel("값")
        
    def update_sensor_list(self, df: pd.DataFrame):
        """
        센서 목록 업데이트
        
        Args:
            df: 데이터프레임
        """
        # timestamp 컬럼 제외한 모든 컬럼을 센서로 간주
        if df is None or df.empty:
            return
            
        sensors = [col for col in df.columns if col != "timestamp"]
        
        # 콤보박스 업데이트
        self.sensor_combo["values"] = sensors
        
        # 선택된 센서가 없거나 유효하지 않은 경우 첫 번째 센서 선택
        if not self.selected_sensor or self.selected_sensor not in sensors:
            if sensors:
                self.sensor_var.set(sensors[0])
                self.selected_sensor = sensors[0]
                
    def on_sensor_selected(self, event=None):
        """센서 선택 이벤트 처리"""
        selected = self.sensor_var.get()
        if selected:
            self.selected_sensor = selected
            
    def toggle_separate_mode(self):
        """분리 모드 전환"""
        self.separate_mode = self.separate_var.get()
        
    def enable_separate_plots(self, sensors: List[str]):
        """
        분리 모드 활성화 및 센서 설정
        
        Args:
            sensors: 표시할 센서 목록
        """
        self.separate_sensors = sensors
        self.separate_var.set(True)
        self.separate_mode = True
        
    def update_graph(self, df: pd.DataFrame):
        """
        그래프 업데이트
        
        Args:
            df: 데이터프레임
        """
        if df is None or df.empty:
            return
            
        try:
            # 센서 목록 업데이트
            self.update_sensor_list(df)
            
            # 그래프 초기화
            self.ax.clear()
            
            if self.separate_mode and self.separate_sensors:
                # 여러 센서 표시 모드
                for sensor in self.separate_sensors:
                    if sensor in df.columns:
                        color = GRAPH_COLORS.get(sensor, "blue")
                        if isinstance(color, str):
                            self.ax.plot(
                                df.index, 
                                df[sensor], 
                                label=sensor,
                                color=color,
                                linewidth=1.5
                            )
                            
                # y축 레이블 설정
                self.ax.set_ylabel("값")
            elif self.selected_sensor and self.selected_sensor in df.columns:
                # 단일 센서 표시 모드
                color = GRAPH_COLORS.get(self.selected_sensor, "blue")
                if isinstance(color, str):
                    self.ax.plot(
                        df.index, 
                        df[self.selected_sensor], 
                        label=self.selected_sensor,
                        color=color,
                        linewidth=1.5
                    )
                    
                # y축 레이블에 단위 추가
                unit = SENSOR_UNITS.get(self.selected_sensor, "")
                if unit:
                    self.ax.set_ylabel(f"{self.selected_sensor} ({unit})")
                else:
                    self.ax.set_ylabel(self.selected_sensor)
            
            # 그래프 설정
            self.ax.set_title("센서 데이터")
            self.ax.set_xlabel("시간")
            self.ax.grid(True, linestyle='--', alpha=0.7)
            
            # 범례 표시
            if self.ax.get_legend_handles_labels()[0]:
                self.ax.legend(loc="upper right")
                
            # x축 레이블 회전
            self.ax.tick_params(axis='x', rotation=45)
            
            # 레이아웃 조정
            self.fig.tight_layout()
            
            # 캔버스 업데이트
            self.canvas.draw()
            
        except Exception as e:
            print(f"그래프 업데이트 오류: {e}")
            import traceback
            print(traceback.format_exc()) 