"""
데이터 테이블 모듈
"""
import tkinter as tk
from tkinter import ttk
import pandas as pd
from typing import List, Dict, Any
from ..config.settings import TABLE_MAX_ROWS

class DataTable(ttk.Frame):
    def __init__(self, parent: tk.Tk):
        """
        데이터 테이블 초기화
        
        Args:
            parent: 부모 위젯
        """
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        
    def setup_ui(self):
        """UI 초기화"""
        # 테이블 프레임
        self.table_frame = ttk.Frame(self)
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 스크롤바
        self.scrollbar_y = ttk.Scrollbar(self.table_frame)
        self.scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.scrollbar_x = ttk.Scrollbar(self.table_frame, orient=tk.HORIZONTAL)
        self.scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 트리뷰
        self.tree = ttk.Treeview(self.table_frame, 
                                yscrollcommand=self.scrollbar_y.set,
                                xscrollcommand=self.scrollbar_x.set)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # 스크롤바 연결
        self.scrollbar_y.config(command=self.tree.yview)
        self.scrollbar_x.config(command=self.tree.xview)
        
    def update_table(self, df: pd.DataFrame):
        """
        테이블 업데이트
        
        Args:
            df: 데이터프레임
        """
        try:
            # 기존 항목 삭제
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            # 컬럼 설정
            self.tree['columns'] = list(df.columns)
            self.tree['show'] = 'headings'
            
            # 컬럼 헤더 설정
            for col in df.columns:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=100)
                
            # 데이터 추가
            if len(df) > TABLE_MAX_ROWS:
                df = df.tail(TABLE_MAX_ROWS)
                
            for idx, row in df.iterrows():
                values = [row[col] for col in df.columns]
                self.tree.insert('', tk.END, values=values)
                
        except Exception as e:
            print(f"테이블 업데이트 오류: {e}")
            
    def clear(self):
        """테이블 초기화"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree['columns'] = [] 