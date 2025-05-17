"""
데이터 테이블 모듈
"""
import tkinter as tk
from tkinter import ttk
import pandas as pd
from typing import Optional, List, Dict, Any
from ..config.settings import TABLE_MAX_ROWS, SENSOR_UNITS

class DataTable(ttk.Treeview):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # 스크롤바 설정
        self.vsb = ttk.Scrollbar(parent, orient="vertical", command=self.yview)
        self.hsb = ttk.Scrollbar(parent, orient="horizontal", command=self.xview)
        self.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)
        
        # 스크롤바 배치
        self.vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 기본 설정
        self["columns"] = ("time", "pt1", "pt2", "type")
        self["show"] = "headings"
        
        # 컬럼 설정
        self.heading("time", text="시간")
        self.heading("pt1", text="PT1")
        self.heading("pt2", text="PT2")
        self.heading("type", text="타입")
        
        # 컬럼 너비 설정
        self.column("time", width=150)
        self.column("pt1", width=200)
        self.column("pt2", width=200)
        self.column("type", width=100)
        
    def update_table(self, df: pd.DataFrame):
        """테이블 업데이트"""
        # 기존 항목 삭제
        for item in self.get_children():
            self.delete(item)
            
        # 새로운 데이터 추가
        for _, row in df.iterrows():
            values = (
                row.get("time", ""),
                str(row.get("pt1", "")),
                str(row.get("pt2", "")),
                row.get("type", "")
            )
            self.insert("", tk.END, values=values)

    def set_columns(self, columns: List[str]):
        """
        테이블 컬럼 설정
        
        Args:
            columns: 컬럼 이름 목록
        """
        self["columns"] = columns
        
        # 기존 트리뷰 설정 초기화
        for col in self["columns"]:
            self.heading(col, text="")
            
        # 트리뷰 컬럼 설정
        self["columns"] = columns
        
        # 컬럼 헤더 설정
        for col in columns:
            # 시간은 기본 헤더
            if col == "time":
                header_text = "시간"
            else:
                # 센서 단위가 있으면 함께 표시
                unit = SENSOR_UNITS.get(col, "")
                header_text = f"{col} ({unit})" if unit else col
                
            # 헤더 설정
            self.heading(col, text=header_text)
            
            # 컬럼 너비 설정 (시간은 넓게, 나머지는 적당히)
            width = 150 if col == "time" else 100
            self.column(col, width=width, anchor=tk.CENTER)
            
    def update_table(self, df: pd.DataFrame):
        """
        테이블 데이터 업데이트
        
        Args:
            df: 업데이트할 데이터프레임
        """
        if df is None or df.empty:
            return
            
        try:
            # 모든 항목 삭제
            for item in self.get_children():
                self.delete(item)
                
            # 컬럼 확인 및 업데이트
            if list(df.columns) != self["columns"]:
                self.set_columns(list(df.columns))
                
            # 테이블 크기 제한
            if len(df) > TABLE_MAX_ROWS:
                df = df.tail(TABLE_MAX_ROWS)
                
            # 행 추가
            for _, row in df.iterrows():
                values = [row[col] if col in row.index else "" for col in self["columns"]]
                
                # 실수 값 포맷팅
                for i, val in enumerate(values):
                    if isinstance(val, float):
                        values[i] = f"{val:.2f}"
                        
                self.insert("", tk.END, values=values)
                
            # 마지막 항목으로 스크롤
            if self.get_children():
                self.see(self.get_children()[-1])
                
        except Exception as e:
            print(f"테이블 업데이트 오류: {e}")
            
    def clear(self):
        """테이블 데이터 초기화"""
        for item in self.get_children():
            self.delete(item) 