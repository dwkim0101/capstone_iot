"""
메인 윈도우 모듈
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import csv
from datetime import datetime
from typing import Optional, Dict, Any
from ..core.data_collector import DataCollector
from ..core.data_processor import DataProcessor
from .graph_view import GraphView
from .led_display import LEDDisplay
from .data_table import DataTable
from .stats_view import StatsView
from ..config.settings import (
    WINDOW_SIZE, WINDOW_TITLE, UPDATE_INTERVAL,
    DEFAULT_BAUD_RATE, DEFAULT_PORT
)

class MainWindow(tk.Tk):
    def __init__(self):
        """메인 윈도우 초기화"""
        super().__init__()
        
        # 윈도우 설정
        self.title(WINDOW_TITLE)
        self.geometry(WINDOW_SIZE)
        
        # 컴포넌트 초기화
        self.data_collector: Optional[DataCollector] = None
        self.data_processor = DataProcessor()
        self.is_collecting = False
        self.collection_thread: Optional[threading.Thread] = None
        
        # UI 초기화
        self.setup_ui()
        
        # 상태바
        self.status_var = tk.StringVar()
        self.status_var.set("준비")
        self.status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def setup_ui(self):
        """UI 초기화"""
        # 메인 프레임
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 상단 프레임 (포트 설정, 시작/중지 버튼)
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=5)
        
        # 포트 설정
        ttk.Label(top_frame, text="포트:").pack(side=tk.LEFT, padx=5)
        self.port_var = tk.StringVar(value=DEFAULT_PORT)
        self.port_entry = ttk.Entry(top_frame, textvariable=self.port_var, width=10)
        self.port_entry.pack(side=tk.LEFT, padx=5)
        
        # 통신 속도 설정
        ttk.Label(top_frame, text="통신 속도:").pack(side=tk.LEFT, padx=5)
        self.baud_var = tk.StringVar(value=str(DEFAULT_BAUD_RATE))
        self.baud_entry = ttk.Entry(top_frame, textvariable=self.baud_var, width=10)
        self.baud_entry.pack(side=tk.LEFT, padx=5)
        
        # 시작/중지 버튼
        self.start_button = ttk.Button(top_frame, text="시작", command=self.start_collection)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(top_frame, text="중지", command=self.stop_collection, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # CSV 저장 버튼
        self.save_button = ttk.Button(top_frame, text="CSV 저장", command=self.save_csv, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        # 중앙 프레임 (그래프, LED, 통계)
        center_frame = ttk.Frame(main_frame)
        center_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 그래프
        self.graph_view = GraphView(center_frame)
        self.graph_view.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # LED 및 통계 프레임
        right_frame = ttk.Frame(center_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5)
        
        # LED 디스플레이
        self.led_display = LEDDisplay(right_frame)
        self.led_display.pack(fill=tk.X, pady=5)
        
        # 통계 뷰
        self.stats_view = StatsView(right_frame)
        self.stats_view.pack(fill=tk.X, pady=5)
        
        # 하단 프레임 (데이터 테이블)
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 데이터 테이블
        self.data_table = DataTable(bottom_frame)
        self.data_table.pack(fill=tk.BOTH, expand=True)
        
        # UI 업데이트 타이머
        self.update_ui()
        
    def start_collection(self):
        """데이터 수집 시작"""
        try:
            port = self.port_var.get()
            baud_rate = int(self.baud_var.get())
            
            self.data_collector = DataCollector(port, baud_rate)
            if not self.data_collector.start():
                messagebox.showerror("오류", "시리얼 포트 연결 실패")
                return
                
            self.is_collecting = True
            self.collection_thread = threading.Thread(target=self.data_collector.collect_data)
            self.collection_thread.daemon = True
            self.collection_thread.start()
            
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.save_button.config(state=tk.DISABLED)
            self.status_var.set("데이터 수집 중...")
            
        except Exception as e:
            messagebox.showerror("오류", f"데이터 수집 시작 실패: {e}")
            
    def stop_collection(self):
        """데이터 수집 중지"""
        if self.data_collector:
            self.data_collector.stop()
            self.is_collecting = False
            
            if self.collection_thread:
                self.collection_thread.join()
                
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.save_button.config(state=tk.NORMAL)
            self.status_var.set("데이터 수집 중지됨")
            
    def save_csv(self):
        """CSV 파일 저장"""
        try:
            if self.data_processor.df.empty:
                messagebox.showwarning("경고", "저장할 데이터가 없습니다.")
                return
                
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                initialfile=f"duet_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            
            if filename:
                self.data_processor.df.to_csv(filename, index=False)
                messagebox.showinfo("성공", "CSV 파일이 저장되었습니다.")
                
        except Exception as e:
            messagebox.showerror("오류", f"CSV 저장 실패: {e}")
            
    def update_ui(self):
        """UI 업데이트"""
        try:
            if self.is_collecting and self.data_collector:
                # 데이터 수집
                data_list = []
                while True:
                    data = self.data_collector.get_data()
                    if data is None:
                        break
                    data_list.append(data)
                    
                if data_list:
                    # 데이터 처리
                    self.data_processor.update_dataframe_batch(data_list)
                    
                    # UI 업데이트
                    df = self.data_processor.get_dataframe()
                    self.graph_view.update_graph(df)
                    self.led_display.update_leds(self.data_processor.get_latest_values())
                    self.stats_view.update_stats(df)
                    self.data_table.update_table(df)
                    
        except Exception as e:
            print(f"UI 업데이트 오류: {e}")
            
        # 다음 업데이트 예약
        self.after(UPDATE_INTERVAL, self.update_ui) 