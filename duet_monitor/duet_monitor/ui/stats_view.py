"""
통계 뷰 모듈
"""
import tkinter as tk
from tkinter import ttk
import pandas as pd
from typing import Dict, Any, List, Optional
from ..config.settings import FONT_FAMILY, SENSOR_UNITS, STATS_FONT

class StatsView(ttk.LabelFrame):
    def __init__(self, parent: tk.Widget):
        """통계 뷰 초기화"""
        super().__init__(parent, text="센서 통계")
        self.parent = parent
        
        # 통계 정보
        self.stats = {}
        self.stats_labels = {}
        
        # UI 초기화
        self.setup_ui()
        
    def setup_ui(self):
        """UI 초기화"""
        # 외부 프레임 (고정 높이)
        outer_frame = ttk.Frame(self)
        outer_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 캔버스 생성
        self.canvas = tk.Canvas(outer_frame, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 스크롤바 생성
        scrollbar = ttk.Scrollbar(outer_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 캔버스와 스크롤바 연결
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # 내부 프레임 생성
        self.inner_frame = ttk.Frame(self.canvas)
        
        # 내부 프레임을 캔버스에 추가
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor=tk.NW)
        
        # 내부 프레임 크기가 변경될 때 스크롤 영역 업데이트
        self.inner_frame.bind('<Configure>', self._configure_inner_frame)
        
        # 마우스 휠 이벤트 바인딩
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # 빈 통계 정보 표시
        self.display_empty_stats()
        
    def _configure_inner_frame(self, event):
        """내부 프레임 크기 변경 이벤트 처리"""
        # 캔버스의 스크롤 영역을 내부 프레임 크기로 설정
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        # 내부 프레임의 너비를 캔버스 너비로 설정
        self.canvas.itemconfig(self.canvas.find_withtag("all")[0], width=self.canvas.winfo_width())
        
    def _on_mousewheel(self, event):
        """마우스 휠 이벤트 처리"""
        if self.canvas.yview() != (0.0, 1.0):  # 스크롤이 필요한 경우에만
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def display_empty_stats(self):
        """빈 통계 정보 표시"""
        empty_label = ttk.Label(self.inner_frame, text="데이터 없음", font=STATS_FONT)
        empty_label.pack(padx=5, pady=20)
        
    def create_stats_section(self, label_text: str):
        """통계 섹션 생성"""
        section_frame = ttk.LabelFrame(self.inner_frame, text=label_text)
        section_frame.pack(fill=tk.X, padx=5, pady=5)
        return section_frame
        
    def update_stats(self, values: Dict[str, Any]):
        """통계 정보 업데이트"""
        if not values:
            return
            
        try:
            # 이전 통계 정보 삭제
            for widget in self.inner_frame.winfo_children():
                widget.destroy()
                
            # 새 통계 정보 표시
            self.stats_labels = {}
            
            # 기본 정보 섹션
            basic_frame = self.create_stats_section("기본 정보")
            
            # 타임스탬프 표시
            if "timestamp" in values:
                self._add_stat_row(basic_frame, "시간", values["timestamp"])
                
            # 숫자 데이터만 필터링
            numeric_values = {
                k: v for k, v in values.items()
                if isinstance(v, (int, float)) and not isinstance(v, bool)
            }
            
            if not numeric_values:
                ttk.Label(
                    self.inner_frame,
                    text="수치 데이터 없음",
                    font=STATS_FONT
                ).pack(padx=5, pady=10)
                return
                
            # 센서 별 그룹화
            sensor_groups = self._group_sensors(numeric_values)
            
            # 각 그룹별로 섹션 생성
            for group_name, sensors in sensor_groups.items():
                group_frame = self.create_stats_section(f"{group_name} 센서")
                
                for sensor in sensors:
                    unit = SENSOR_UNITS.get(sensor, "")
                    unit_text = f" {unit}" if unit else ""
                    
                    if sensor in values:
                        value = values[sensor]
                        if isinstance(value, float):
                            value = f"{value:.2f}"
                        self._add_stat_row(group_frame, f"{sensor}{unit_text}", value)
                        
            # 스크롤 영역 업데이트
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
        except Exception as e:
            print(f"통계 업데이트 오류: {e}")
            # 오류 시 기본 메시지 표시
            for widget in self.inner_frame.winfo_children():
                widget.destroy()
            ttk.Label(
                self.inner_frame,
                text=f"통계 표시 오류: {e}",
                font=STATS_FONT
            ).pack(padx=5, pady=20)
            
    def _add_stat_row(self, parent: tk.Widget, label: str, value: Any):
        """통계 행 추가"""
        row_frame = ttk.Frame(parent)
        row_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # 레이블
        label_widget = ttk.Label(row_frame, text=f"{label}:", anchor=tk.W, width=15)
        label_widget.pack(side=tk.LEFT, padx=5)
        
        # 값
        value_str = str(value)
        value_widget = ttk.Label(row_frame, text=value_str, anchor=tk.W)
        value_widget.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 딕셔너리에 저장
        self.stats_labels[label] = (label_widget, value_widget)
        
    def _group_sensors(self, values: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        센서 그룹화
        
        Args:
            values: 값 딕셔너리
            
        Returns:
            그룹화된 센서 딕셔너리
        """
        groups = {
            "환경": [],
            "파티클": [],
            "기타": []
        }
        
        for sensor in values.keys():
            if sensor in ["temperature", "humidity", "pressure"]:
                groups["환경"].append(sensor)
            elif sensor.startswith("pt") or sensor.startswith("pm"):
                groups["파티클"].append(sensor)
            else:
                groups["기타"].append(sensor)
                
        # 비어있는 그룹 제거
        return {k: v for k, v in groups.items() if v} 