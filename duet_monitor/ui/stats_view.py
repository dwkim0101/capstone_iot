"""
통계 뷰 모듈
"""
import tkinter as tk
from tkinter import ttk
import pandas as pd
from typing import Dict, Any
from ..config.settings import STATS_FONT

class StatsView(ttk.Frame):
    def __init__(self, parent: tk.Tk):
        """
        통계 뷰 초기화
        
        Args:
            parent: 부모 위젯
        """
        super().__init__(parent)
        self.parent = parent
        self.stats_labels: Dict[str, ttk.Label] = {}
        self.setup_ui()
        
    def setup_ui(self):
        """UI 초기화"""
        # 통계 프레임
        self.stats_frame = ttk.Frame(self)
        self.stats_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 제목
        ttk.Label(self.stats_frame, text="통계", font=STATS_FONT).pack(pady=5)
        
    def update_stats(self, df: pd.DataFrame):
        """
        통계 업데이트
        
        Args:
            df: 데이터프레임
        """
        try:
            # 기존 레이블 삭제
            for label in self.stats_labels.values():
                label.destroy()
            self.stats_labels.clear()
            
            if df.empty:
                return
                
            # 수치형 컬럼만 선택
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
            
            # 통계 계산
            stats = df[numeric_cols].describe()
            
            # 통계 표시
            row = 1
            for col in numeric_cols:
                # 컬럼 이름
                ttk.Label(self.stats_frame, text=col).grid(row=row, column=0, padx=5, pady=2)
                
                # 평균
                ttk.Label(self.stats_frame, text="평균:").grid(row=row, column=1, padx=5, pady=2)
                mean_label = ttk.Label(self.stats_frame, text=f"{stats[col]['mean']:.2f}")
                mean_label.grid(row=row, column=2, padx=5, pady=2)
                
                # 최대
                ttk.Label(self.stats_frame, text="최대:").grid(row=row, column=3, padx=5, pady=2)
                max_label = ttk.Label(self.stats_frame, text=f"{stats[col]['max']:.2f}")
                max_label.grid(row=row, column=4, padx=5, pady=2)
                
                # 최소
                ttk.Label(self.stats_frame, text="최소:").grid(row=row, column=5, padx=5, pady=2)
                min_label = ttk.Label(self.stats_frame, text=f"{stats[col]['min']:.2f}")
                min_label.grid(row=row, column=6, padx=5, pady=2)
                
                # 레이블 저장
                self.stats_labels[f"{col}_mean"] = mean_label
                self.stats_labels[f"{col}_max"] = max_label
                self.stats_labels[f"{col}_min"] = min_label
                
                row += 1
                
        except Exception as e:
            print(f"통계 업데이트 오류: {e}")
            
    def clear(self):
        """통계 초기화"""
        for label in self.stats_labels.values():
            label.destroy()
        self.stats_labels.clear() 