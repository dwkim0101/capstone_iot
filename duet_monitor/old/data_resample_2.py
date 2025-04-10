import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import os
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec

print("TelosAir Duet 데이터 분석 도구 시작...")

# ----- 설정 및 초기화 -----
DEFAULT_RESAMPLE_PERIOD = "10s"  # 기본 재샘플링 주기
DEFAULT_RESAMPLE_METHOD = "mean"  # 기본 재샘플링 방법

class DuetDataAnalyzer:
    def __init__(self):
        # GUI 초기화
        self.root = tk.Tk()
        self.root.title("TelosAir Duet 데이터 분석기")
        self.root.geometry("1200x800")  # 더 큰 창 크기로 변경
        self.setup_gui()
        
    def setup_gui(self):
        """메인 GUI 설정"""
        # 상단 프레임 (파일 선택 및 설정)
        self.top_frame = tk.Frame(self.root)
        self.top_frame.pack(pady=10, fill=tk.X, padx=20)
        
        # 파일 선택 버튼
        self.file_frame = tk.Frame(self.top_frame)
        self.file_frame.pack(side=tk.LEFT, padx=5)
        
        self.file_label = tk.Label(self.file_frame, text="데이터 파일: 선택되지 않음")
        self.file_label.pack(side=tk.LEFT)
        
        self.file_btn = tk.Button(self.file_frame, text="파일 선택", command=self.load_file)
        self.file_btn.pack(side=tk.LEFT, padx=5)
        
        # 재샘플링 설정 프레임
        self.resample_frame = tk.Frame(self.top_frame)
        self.resample_frame.pack(side=tk.LEFT, padx=20)
        
        # 재샘플링 주기
        tk.Label(self.resample_frame, text="재샘플링 주기:").grid(row=0, column=0, padx=5, pady=5)
        self.period_var = tk.StringVar(value=DEFAULT_RESAMPLE_PERIOD)
        periods = ["1s", "5s", "10s", "30s", "1min", "5min", "10min", "30min", "1h"]
        self.period_menu = tk.OptionMenu(self.resample_frame, self.period_var, *periods)
        self.period_menu.grid(row=0, column=1, padx=5, pady=5)
        
        # 재샘플링 방법
        tk.Label(self.resample_frame, text="재샘플링 방법:").grid(row=1, column=0, padx=5, pady=5)
        self.method_var = tk.StringVar(value=DEFAULT_RESAMPLE_METHOD)
        methods = ["mean", "median", "min", "max"]
        self.method_menu = tk.OptionMenu(self.resample_frame, self.method_var, *methods)
        self.method_menu.grid(row=1, column=1, padx=5, pady=5)
        
        # 분석 버튼
        self.analyze_btn = tk.Button(self.resample_frame, text="데이터 분석", 
                                    command=self.analyze_data, state=tk.DISABLED)
        self.analyze_btn.grid(row=0, column=2, rowspan=2, padx=10, pady=5)
        
        # 저장 버튼
        self.save_btn = tk.Button(self.resample_frame, text="CSV 저장", 
                                 command=self.save_data, state=tk.DISABLED)
        self.save_btn.grid(row=0, column=3, rowspan=2, padx=10, pady=5)
        
        # 메인 콘텐츠 영역 (데이터 테이블 + 그래프)
        self.content_frame = tk.Frame(self.root, bg='white')
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 대시보드가 표시될 캔버스 영역
        self.canvas_frame = tk.Frame(self.content_frame, bg='white')
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # 기본 메시지 표시
        self.info_label = tk.Label(self.canvas_frame, text="파일을 선택하고 '데이터 분석' 버튼을 클릭하면 모든 데이터가 여기에 표시됩니다.", 
                                  bg='white', font=('Arial', 14))
        self.info_label.pack(expand=True)
        
        # 상태 표시줄
        self.status_var = tk.StringVar(value="파일을 선택해주세요.")
        self.status_label = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
        
    def load_file(self):
        """데이터 파일 로드"""
        try:
            # 파일 대화상자 열기
            current_dir = os.getcwd()
            file_path = filedialog.askopenfilename(
                title="데이터 파일 선택",
                initialdir=current_dir,
                filetypes=[("CSV 파일", "*.csv"), ("모든 파일", "*.*")]
            )
            
            if not file_path:
                return
                
            self.file_label.config(text=f"파일: {os.path.basename(file_path)}")
            self.status_var.set("파일을 로드하는 중...")
            self.root.update()
            
            # 데이터 로드
            self.df = pd.read_csv(file_path)
            
            # 타임스탬프 열 자동 감지
            timestamp_cols = [col for col in self.df.columns if 'time' in col.lower() or 'date' in col.lower()]
            self.timestamp_col = timestamp_cols[0] if timestamp_cols else self.df.columns[0]
            
            # 시리얼 번호 열 자동 감지
            id_cols = [col for col in self.df.columns if 'id' in col.lower() or 'serial' in col.lower() or 'device' in col.lower()]
            self.id_col = id_cols[0] if id_cols else None
            
            # 타임스탬프를 datetime으로 변환
            try:
                self.df[self.timestamp_col] = pd.to_datetime(self.df[self.timestamp_col])
            except:
                self.df[self.timestamp_col] = pd.to_datetime(self.df[self.timestamp_col], format="mixed")
            
            # 데이터 미리보기
            self.status_var.set(f"데이터 로드 완료: {len(self.df)}행 {len(self.df.columns)}열")
            
            # 버튼 활성화
            self.analyze_btn.config(state=tk.NORMAL)
            self.save_btn.config(state=tk.NORMAL)
            
            # 데이터 요약 정보 표시
            self.show_data_summary()
            
        except Exception as e:
            messagebox.showerror("오류", f"파일 로드 중 오류 발생: {str(e)}")
            self.status_var.set("파일 로드 실패")
    
    def show_data_summary(self):
        """데이터 요약 정보 표시"""
        # 이전 내용 지우기
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()
        
        # 데이터 요약 프레임
        summary_frame = tk.Frame(self.canvas_frame, bg='white')
        summary_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 데이터 행/열 정보
        tk.Label(summary_frame, text=f"데이터 크기: {len(self.df)}행 × {len(self.df.columns)}열", 
                bg='white', font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # 타임스탬프 범위
        time_range = f"시간 범위: {self.df[self.timestamp_col].min()} ~ {self.df[self.timestamp_col].max()}"
        tk.Label(summary_frame, text=time_range, bg='white', font=('Arial', 12)).grid(row=1, column=0, sticky=tk.W, pady=2)
        
        # 장치 ID 정보 (있는 경우)
        if self.id_col:
            device_ids = self.df[self.id_col].unique()
            id_info = f"장치 ID: {', '.join(map(str, device_ids))} (총 {len(device_ids)}개)"
            tk.Label(summary_frame, text=id_info, bg='white', font=('Arial', 12)).grid(row=2, column=0, sticky=tk.W, pady=2)
        
        # 데이터 테이블 (상위 10개 행)
        table_frame = tk.Frame(self.canvas_frame, bg='white')
        table_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(table_frame, text="데이터 미리보기 (상위 10행):", 
               bg='white', font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=5)
        
        # 간단한 테이블 생성
        table = tk.Frame(table_frame, bg='white')
        table.pack(fill=tk.X, pady=5)
        
        # 열 이름
        for i, col in enumerate(self.df.columns):
            tk.Label(table, text=col, bg='#f0f0f0', relief=tk.RIDGE, width=15, 
                   font=('Arial', 10, 'bold')).grid(row=0, column=i, sticky=tk.W+tk.E)
        
        # 데이터 행
        for row_idx in range(min(10, len(self.df))):
            for col_idx, col in enumerate(self.df.columns):
                value = str(self.df.iloc[row_idx, col_idx])
                if len(value) > 20:
                    value = value[:20] + "..."
                tk.Label(table, text=value, bg='white', relief=tk.RIDGE, width=15,
                       font=('Arial', 10)).grid(row=row_idx+1, column=col_idx, sticky=tk.W+tk.E)
    
    def analyze_data(self):
        """모든 데이터를 자동으로 분석하고 대시보드 표시"""
        try:
            if not hasattr(self, 'df'):
                messagebox.showwarning("경고", "데이터가 로드되지 않았습니다.")
                return
                
            self.status_var.set("데이터 분석 중...")
            self.root.update()
            
            # 타임스탬프를 인덱스로 설정
            df_indexed = self.df.set_index(self.timestamp_col)
            
            # 재샘플링 수행
            period = self.period_var.get()
            method = self.method_var.get()
            
            # 이전 대시보드 내용 지우기
            for widget in self.canvas_frame.winfo_children():
                widget.destroy()
            
            # 대시보드 헤더
            header_frame = tk.Frame(self.canvas_frame, bg='white')
            header_frame.pack(fill=tk.X, padx=10, pady=10)
            
            analysis_title = f"{period} 간격으로 {method} 재샘플링 결과"
            tk.Label(header_frame, text=analysis_title, bg='white', 
                   font=('Arial', 14, 'bold')).pack(anchor=tk.W)
            
            # 대시보드 시각화 영역
            if self.id_col:
                # 다중 장치 데이터 처리
                self.resampled_dfs = {}
                groups = self.df[self.id_col].unique()
                
                for group in groups:
                    group_df = df_indexed[df_indexed[self.id_col] == group]
                    
                    # object 열 제거 (재샘플링에 문제가 될 수 있음)
                    for col in group_df.select_dtypes(include=['object']).columns:
                        if col != self.id_col:
                            group_df = group_df.drop(columns=[col])
                    
                    # 재샘플링
                    if method == "mean":
                        resampled = group_df.resample(period).mean()
                    elif method == "median":
                        resampled = group_df.resample(period).median()
                    elif method == "min":
                        resampled = group_df.resample(period).min()
                    elif method == "max":
                        resampled = group_df.resample(period).max()
                    
                    self.resampled_dfs[group] = resampled
                
                # 대시보드 생성 (모든 열에 대해 다중 장치 데이터 시각화)
                self.create_multi_device_dashboard()
            else:
                # 단일 데이터셋 재샘플링
                if method == "mean":
                    self.resampled_df = df_indexed.resample(period).mean()
                elif method == "median":
                    self.resampled_df = df_indexed.resample(period).median()
                elif method == "min":
                    self.resampled_df = df_indexed.resample(period).min()
                elif method == "max":
                    self.resampled_df = df_indexed.resample(period).max()
                
                # 단일 데이터셋 대시보드 생성
                self.create_single_dataset_dashboard()
            
            self.status_var.set(f"데이터 분석 완료: {period} 간격으로 {method} 재샘플링")
            
        except Exception as e:
            messagebox.showerror("오류", f"데이터 분석 중 오류 발생: {str(e)}")
            self.status_var.set("데이터 분석 실패")
    
    def create_single_dataset_dashboard(self):
        """단일 데이터셋에 대한 대시보드 생성"""
        # 수치형 열만 필터링
        numeric_cols = self.resampled_df.select_dtypes(include=np.number).columns.tolist()
        
        if not numeric_cols:
            tk.Label(self.canvas_frame, text="시각화할 수치 데이터가 없습니다.", 
                   bg='white', font=('Arial', 12)).pack(pady=20)
            return
        
        # 대시보드 스크롤 영역 생성
        canvas_container = tk.Frame(self.canvas_frame)
        canvas_container.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(canvas_container, bg='white')
        scrollbar = tk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 통계 요약 테이블
        stats_frame = tk.Frame(scrollable_frame, bg='white')
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(stats_frame, text="데이터 통계 요약", bg='white', 
               font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=5)
        
        # 통계 데이터 테이블 생성
        stats_table = tk.Frame(stats_frame, bg='white')
        stats_table.pack(fill=tk.X, pady=5)
        
        # 통계 항목 열 헤더
        tk.Label(stats_table, text="항목", bg='#f0f0f0', relief=tk.RIDGE, width=15, 
               font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W+tk.E)
        
        for i, col in enumerate(numeric_cols):
            tk.Label(stats_table, text=col, bg='#f0f0f0', relief=tk.RIDGE, width=15, 
                   font=('Arial', 10, 'bold')).grid(row=0, column=i+1, sticky=tk.W+tk.E)
        
        # 통계 행 데이터
        stats_rows = ["평균", "최소값", "최대값", "표준편차", "중앙값"]
        stats_funcs = [np.mean, np.min, np.max, np.std, np.median]
        
        for row_idx, (row_name, func) in enumerate(zip(stats_rows, stats_funcs)):
            tk.Label(stats_table, text=row_name, bg='#f0f0f0', relief=tk.RIDGE, width=15,
                   font=('Arial', 10, 'bold')).grid(row=row_idx+1, column=0, sticky=tk.W+tk.E)
            
            for col_idx, col in enumerate(numeric_cols):
                val = func(self.resampled_df[col].dropna())
                formatted_val = f"{val:.4g}" if abs(val) < 1000 else f"{val:.2e}"
                tk.Label(stats_table, text=formatted_val, bg='white', relief=tk.RIDGE, width=15,
                       font=('Arial', 10)).grid(row=row_idx+1, column=col_idx+1, sticky=tk.W+tk.E)
        
        # 그래프 생성 (열당 하나의 그래프)
        for i, col in enumerate(numeric_cols):
            graph_frame = tk.Frame(scrollable_frame, bg='white', bd=1, relief=tk.GROOVE)
            graph_frame.pack(fill=tk.X, padx=10, pady=10)
            
            # 그래프 제목
            tk.Label(graph_frame, text=f"{col} 시계열 그래프", bg='white', 
                   font=('Arial', 12, 'bold')).pack(anchor=tk.W, padx=10, pady=5)
            
            # 그래프 생성
            fig = Figure(figsize=(10, 4), dpi=100)
            ax = fig.add_subplot(111)
            
            # 데이터 플롯
            ax.plot(self.resampled_df.index, self.resampled_df[col], 'b-')
            ax.set_ylabel(col)
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # 날짜 포맷 자동 조정
            fig.autofmt_xdate()
            
            # 그래프를 Tkinter 캔버스에 삽입
            canvas = FigureCanvasTkAgg(fig, master=graph_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def create_multi_device_dashboard(self):
        """다중 장치 데이터에 대한 대시보드 생성"""
        # 샘플 데이터프레임을 이용해 열 이름 가져오기
        sample_df = next(iter(self.resampled_dfs.values()))
        numeric_cols = sample_df.select_dtypes(include=np.number).columns.tolist()
        
        if not numeric_cols:
            tk.Label(self.canvas_frame, text="시각화할 수치 데이터가 없습니다.", 
                   bg='white', font=('Arial', 12)).pack(pady=20)
            return
        
        # 대시보드 스크롤 영역 생성
        canvas_container = tk.Frame(self.canvas_frame)
        canvas_container.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(canvas_container, bg='white')
        scrollbar = tk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 장치별 요약 통계
        stats_frame = tk.Frame(scrollable_frame, bg='white')
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(stats_frame, text="장치별 데이터 요약", bg='white', 
               font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=5)
        
        # 각 장치별 평균값 테이블
        for col in numeric_cols:
            col_frame = tk.Frame(stats_frame, bg='white', bd=1, relief=tk.GROOVE)
            col_frame.pack(fill=tk.X, pady=5)
            
            tk.Label(col_frame, text=f"{col} 통계", bg='#f0f0f0', 
                   font=('Arial', 11, 'bold')).pack(anchor=tk.W, padx=10, pady=5)
            
            stats_table = tk.Frame(col_frame, bg='white')
            stats_table.pack(fill=tk.X, padx=10, pady=5)
            
            # 헤더 행
            tk.Label(stats_table, text="장치 ID", bg='#f0f0f0', relief=tk.RIDGE, width=15, 
                   font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W+tk.E)
            
            stats_names = ["평균", "최소값", "최대값", "표준편차", "데이터 수"]
            for i, stat in enumerate(stats_names):
                tk.Label(stats_table, text=stat, bg='#f0f0f0', relief=tk.RIDGE, width=12, 
                       font=('Arial', 10, 'bold')).grid(row=0, column=i+1, sticky=tk.W+tk.E)
            
            # 각 장치별 통계
            for row_idx, (device_id, df) in enumerate(self.resampled_dfs.items()):
                tk.Label(stats_table, text=str(device_id), bg='#f0f0f0', relief=tk.RIDGE, width=15,
                       font=('Arial', 10, 'bold')).grid(row=row_idx+1, column=0, sticky=tk.W+tk.E)
                
                if col in df.columns:
                    # 통계값 계산
                    series = df[col].dropna()
                    mean_val = series.mean()
                    min_val = series.min()
                    max_val = series.max()
                    std_val = series.std()
                    count_val = series.count()
                    
                    # 값 포맷팅 및 표시
                    stats = [mean_val, min_val, max_val, std_val, count_val]
                    for i, val in enumerate(stats):
                        formatted_val = f"{val:.4g}" if i < 4 and abs(val) < 1000 else f"{val:.2e}" if i < 4 else str(int(val))
                        tk.Label(stats_table, text=formatted_val, bg='white', relief=tk.RIDGE, width=12,
                               font=('Arial', 10)).grid(row=row_idx+1, column=i+1, sticky=tk.W+tk.E)
                else:
                    # 열이 없는 경우
                    for i in range(5):
                        tk.Label(stats_table, text="-", bg='white', relief=tk.RIDGE, width=12,
                               font=('Arial', 10)).grid(row=row_idx+1, column=i+1, sticky=tk.W+tk.E)
        
        # 열별 시계열 그래프 (모든 장치 함께 표시)
        for col in numeric_cols:
            graph_frame = tk.Frame(scrollable_frame, bg='white', bd=1, relief=tk.GROOVE)
            graph_frame.pack(fill=tk.X, padx=10, pady=10)
            
            # 그래프 제목
            tk.Label(graph_frame, text=f"{col} 시계열 그래프 (모든 장치)", bg='white', 
                   font=('Arial', 12, 'bold')).pack(anchor=tk.W, padx=10, pady=5)
            
            # 그래프 생성
            fig = Figure(figsize=(10, 4), dpi=100)
            ax = fig.add_subplot(111)
            
            # 각 장치의 데이터 플롯
            for device_id, df in self.resampled_dfs.items():
                if col in df.columns:
                    ax.plot(df.index, df[col], '-', label=f'장치 {device_id}')
            
            ax.set_ylabel(col)
            ax.grid(True, linestyle='--', alpha=0.7)
            ax.legend()
            
            # 날짜 포맷 자동 조정
            fig.autofmt_xdate()
            
            # 그래프를 Tkinter 캔버스에 삽입
            canvas = FigureCanvasTkAgg(fig, master=graph_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 장치 간 비교 그래프 (상관관계)
        if len(self.resampled_dfs) >= 2:
            for col in numeric_cols:
                # 모든 장치 쌍에 대해 비교 그래프 생성
                devices = list(self.resampled_dfs.keys())
                
                for i in range(len(devices)):
                    for j in range(i+1, len(devices)):
                        device1 = devices[i]
                        device2 = devices[j]
                        
                        df1 = self.resampled_dfs[device1]
                        df2 = self.resampled_dfs[device2]
                        
                        # 두 장치 모두 해당 열이 있는지 확인
                        if col in df1.columns and col in df2.columns:
                            # 시간 인덱스에 따라 데이터 정렬 및 결합
                            common_df = pd.DataFrame({
                                'x': df1[col],
                                'y': df2[col]
                            }).dropna()
                            
                            # 데이터가 충분한지 확인
                            if len(common_df) >= 5:
                                compare_frame = tk.Frame(scrollable_frame, bg='white', bd=1, relief=tk.GROOVE)
                                compare_frame.pack(fill=tk.X, padx=10, pady=10)
                                
                                # 그래프 제목
                                tk.Label(compare_frame, text=f"{col}: 장치 {device1} vs 장치 {device2} 비교", 
                                       bg='white', font=('Arial', 12, 'bold')).pack(anchor=tk.W, padx=10, pady=5)
                                
                                # 상관관계 계산
                                corr = common_df['x'].corr(common_df['y'])
                                tk.Label(compare_frame, text=f"상관계수: {corr:.4f}", 
                                       bg='white', font=('Arial', 10, 'italic')).pack(anchor=tk.W, padx=10)
                                
                                # 산점도 그래프 생성
                                fig = Figure(figsize=(8, 6), dpi=100)
                                ax = fig.add_subplot(111)
                                
                                ax.scatter(common_df['x'], common_df['y'], alpha=0.7)
                                
                                # 동일선 표시
                                min_val = min(common_df['x'].min(), common_df['y'].min())
                                max_val = max(common_df['x'].max(), common_df['y'].max())
                                ax.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5)
                                
                                ax.set_xlabel(f"장치 {device1}: {col}")
                                ax.set_ylabel(f"장치 {device2}: {col}")
                                ax.grid(True, linestyle='--', alpha=0.5)
                                
                                # 그래프를 Tkinter 캔버스에 삽입
                                canvas = FigureCanvasTkAgg(fig, master=compare_frame)
                                canvas.draw()
                                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def save_data(self):
        """재샘플링된 데이터 저장"""
        try:
            if hasattr(self, 'resampled_df'):
                # 단일 데이터셋 저장
                save_path = filedialog.asksaveasfilename(
                    title="재샘플링된 데이터 저장",
                    defaultextension=".csv",
                    filetypes=[("CSV 파일", "*.csv"), ("모든 파일", "*.*")]
                )
                
                if save_path:
                    self.resampled_df.to_csv(save_path)
                    self.status_var.set(f"데이터가 {save_path}에 저장되었습니다.")
                
            elif hasattr(self, 'resampled_dfs'):
                # 다중 데이터셋 저장
                save_path = filedialog.asksaveasfilename(
                    title="재샘플링된 데이터 저장",
                    defaultextension=".csv",
                    filetypes=[("CSV 파일", "*.csv"), ("모든 파일", "*.*")]
                )
                
                if save_path:
                    # 모든 데이터셋을 하나로 결합
                    combined_df = pd.concat([df.assign(**{self.id_col: group}) 
                                           for group, df in self.resampled_dfs.items()])
                    combined_df.to_csv(save_path)
                    self.status_var.set(f"데이터가 {save_path}에 저장되었습니다.")
            
            else:
                messagebox.showwarning("경고", "저장할 데이터가 없습니다. 먼저 데이터를 분석하세요.")
        
        except Exception as e:
            messagebox.showerror("오류", f"데이터 저장 중 오류 발생: {str(e)}")
    
    def run(self):
        """애플리케이션 실행"""
        self.root.mainloop()

# 메인 실행 부분
if __name__ == "__main__":
    app = DuetDataAnalyzer()
    app.run()
