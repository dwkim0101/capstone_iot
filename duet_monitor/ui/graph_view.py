"""
그래프 뷰 모듈
"""
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
from typing import List, Dict, Any
from ..config.settings import MAX_DATA_POINTS, GRAPH_COLORS
from ..utils.helpers import get_unit_for_sensor

class GraphView(ttk.Frame):
    def __init__(self, parent: tk.Tk):
        """
        그래프 뷰 초기화
        
        Args:
            parent: 부모 위젯
        """
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        
    def setup_ui(self):
        """UI 초기화"""
        # 컬럼 선택 프레임
        self.column_frame = ttk.Frame(self)
        self.column_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(self.column_frame, text="표시할 컬럼:").pack(side=tk.LEFT)
        self.column_listbox = tk.Listbox(self.column_frame, selectmode=tk.MULTIPLE, height=5)
        self.column_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 그래프 프레임
        self.graph_frame = ttk.Frame(self)
        self.graph_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 그래프 생성
        self.fig = Figure(figsize=(8, 6))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 그래프 스타일 설정
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.ax.set_xlabel('시간')
        self.ax.set_ylabel('값')
        
        # 컬럼 선택 이벤트 바인딩
        self.column_listbox.bind('<<ListboxSelect>>', self.on_column_select)
        
    def update_columns(self, columns: List[str]):
        """
        컬럼 목록 업데이트
        
        Args:
            columns: 컬럼 이름 리스트
        """
        self.column_listbox.delete(0, tk.END)
        for col in columns:
            self.column_listbox.insert(tk.END, col)
            
    def on_column_select(self, event):
        """컬럼 선택 이벤트 핸들러"""
        self.update_graph()
        
    def update_graph(self, df: pd.DataFrame = None):
        """
        그래프 업데이트
        
        Args:
            df: 데이터프레임
        """
        if df is None or df.empty:
            return
            
        try:
            # 선택된 컬럼 가져오기
            selected_indices = self.column_listbox.curselection()
            if not selected_indices:
                return
                
            selected_columns = [self.column_listbox.get(i) for i in selected_indices]
            
            # 데이터 샘플링
            if len(df) > MAX_DATA_POINTS:
                df = df.tail(MAX_DATA_POINTS)
                
            # 그래프 초기화
            self.ax.clear()
            self.ax.grid(True, linestyle='--', alpha=0.7)
            
            # 타임스탬프 처리
            if 'timestamp' in df.columns:
                timestamps = pd.to_datetime(df['timestamp'])
            else:
                timestamps = pd.date_range(start='now', periods=len(df), freq='S')
                
            # 데이터 플로팅
            for i, col in enumerate(selected_columns):
                if col in df.columns:
                    data = df[col].dropna()
                    if not data.empty:
                        color = GRAPH_COLORS[i % len(GRAPH_COLORS)]
                        unit = get_unit_for_sensor(col)
                        label = f"{col} [{unit}]" if unit else col
                        self.ax.plot(timestamps, data, label=label, color=color, linewidth=1)
                        
            # 그래프 스타일 설정
            self.ax.set_xlabel('시간')
            self.ax.set_ylabel('값')
            self.ax.legend(loc='upper left')
            self.ax.tick_params(axis='x', rotation=45)
            
            # 그래프 업데이트
            self.fig.tight_layout()
            self.canvas.draw_idle()
            
        except Exception as e:
            print(f"그래프 업데이트 오류: {e}")
            
    def clear(self):
        """그래프 초기화"""
        self.ax.clear()
        self.canvas.draw_idle() 