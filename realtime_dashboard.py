import json
import datetime
import pandas as pd
import numpy as np
import serial
import serial.tools.list_ports
import time
import os
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import threading
import queue
import matplotlib.animation as animation
import matplotlib.dates as mdates
import matplotlib as mpl

# 한글 폰트 문제 해결
mpl.rcParams['font.family'] = 'AppleGothic' if 'AppleGothic' in mpl.font_manager.get_font_names() else 'NanumGothic'
mpl.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

# 전역 상수
MAX_DATA_POINTS = 500  # 그래프에 표시할 최대 데이터 포인트 수
UPDATE_INTERVAL = 500  # 대시보드 업데이트 간격 (밀리초)

class RealTimeDuetMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("TelosAir Duet 실시간 모니터링 대시보드")
        self.root.geometry("1280x800")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 데이터 저장 변수
        self.serial_port = None
        self.is_collecting = False
        self.data_queue = queue.Queue()
        self.all_data = []  # 모든 수집된 데이터
        self.df = pd.DataFrame()  # 데이터프레임
        
        # 그래프 설정 변수
        self.selected_columns = []
        self.plot_data = {}  # 그래프용 데이터 저장
        self.auto_update_graph = True  # 그래프 자동 업데이트 옵션
        
        # 메인 UI 구성
        self.setup_ui()
        
        # 시리얼 포트 목록 업데이트
        self.update_port_list()
    
    def setup_ui(self):
        """UI 구성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 상단 제어 패널
        control_frame = ttk.LabelFrame(main_frame, text="제어 패널")
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 포트 설정 프레임
        port_frame = ttk.Frame(control_frame)
        port_frame.pack(side=tk.LEFT, padx=10, pady=5)
        
        ttk.Label(port_frame, text="시리얼 포트:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.port_combobox = ttk.Combobox(port_frame, width=20, state="readonly")
        self.port_combobox.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(port_frame, text="새로고침", command=self.update_port_list).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(port_frame, text="속도(baud):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.baud_combobox = ttk.Combobox(port_frame, width=10, values=["9600", "19200", "38400", "57600", "115200"])
        self.baud_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.baud_combobox.set("9600")  # 기본값
        
        # 데이터 수집 컨트롤 프레임
        collect_frame = ttk.Frame(control_frame)
        collect_frame.pack(side=tk.LEFT, padx=20, pady=5)
        
        self.start_button = ttk.Button(collect_frame, text="수집 시작", command=self.start_collecting)
        self.start_button.grid(row=0, column=0, padx=5, pady=5)
        
        # 중지 버튼에 커맨드 업데이트 - 더 안정적인 방식으로 변경
        self.stop_button = ttk.Button(collect_frame, text="수집 중지", command=self.request_stop_collecting, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5, pady=5)
        
        # 데이터 저장 프레임
        save_frame = ttk.Frame(control_frame)
        save_frame.pack(side=tk.LEFT, padx=20, pady=5)
        
        self.save_csv_button = ttk.Button(save_frame, text="CSV 저장", command=self.save_to_csv, state=tk.DISABLED)
        self.save_csv_button.grid(row=0, column=0, padx=5, pady=5)
        
        # 상태 표시 영역
        self.status_var = tk.StringVar(value="상태: 준비")
        status_label = ttk.Label(control_frame, textvariable=self.status_var)
        status_label.pack(side=tk.RIGHT, padx=20, pady=5)
        
        # 데이터와 그래프를 포함할 노트북
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 1. 데이터 테이블 탭
        self.table_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.table_frame, text="실시간 데이터")
        
        # 데이터 테이블 설정
        self.setup_data_table()
        
        # 2. 그래프 탭
        self.graph_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.graph_frame, text="실시간 그래프")
        
        # 그래프 설정
        self.setup_graphs()
        
        # 3. 통계 탭
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text="데이터 통계")
        
        # 통계 설정
        self.setup_stats_view()
    
    def setup_data_table(self):
        """데이터 테이블 UI 설정"""
        # 프레임 구성
        table_control = ttk.Frame(self.table_frame)
        table_control.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(table_control, text="표시 행 수:").pack(side=tk.LEFT, padx=5)
        self.rows_spinbox = ttk.Spinbox(table_control, from_=10, to=100, width=5, increment=10)
        self.rows_spinbox.pack(side=tk.LEFT, padx=5)
        self.rows_spinbox.set(20)  # 기본값
        
        # 데이터 테이블 (Treeview 사용)
        table_container = ttk.Frame(self.table_frame)
        table_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 스크롤바
        scrollbar_y = ttk.Scrollbar(table_container)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scrollbar_x = ttk.Scrollbar(table_container, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Treeview 생성
        self.data_table = ttk.Treeview(table_container, yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        self.data_table.pack(fill=tk.BOTH, expand=True)
        
        # 스크롤바 연결
        scrollbar_y.config(command=self.data_table.yview)
        scrollbar_x.config(command=self.data_table.xview)
        
        # 기본 열 구성
        self.data_table['columns'] = ('timestamp',)
        self.data_table.column('#0', width=50, stretch=tk.NO)
        self.data_table.column('timestamp', width=150, anchor=tk.W)
        
        self.data_table.heading('#0', text='번호')
        self.data_table.heading('timestamp', text='타임스탬프')
    
    def setup_graphs(self):
        """실시간 그래프 UI 설정"""
        # 그래프 컨트롤 프레임
        graph_control = ttk.Frame(self.graph_frame)
        graph_control.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(graph_control, text="표시할 센서 데이터:").pack(side=tk.LEFT, padx=5)
        self.column_listbox = tk.Listbox(graph_control, selectmode=tk.MULTIPLE, height=4)
        self.column_listbox.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        ttk.Button(graph_control, text="그래프 업데이트", command=self.update_graph_selection).pack(side=tk.LEFT, padx=10)
        
        # 자동 업데이트 체크박스 추가
        self.auto_update_var = tk.BooleanVar(value=True)
        auto_update_check = ttk.Checkbutton(
            graph_control, 
            text="자동 업데이트", 
            variable=self.auto_update_var,
            command=self.toggle_auto_update
        )
        auto_update_check.pack(side=tk.LEFT, padx=10)
        
        # 테스트 데이터 생성 버튼 (실제 연결 없이 테스트용)
        ttk.Button(graph_control, text="테스트 데이터", command=self.generate_test_data).pack(side=tk.RIGHT, padx=10)
        
        # 그래프 컨테이너
        self.graph_container = ttk.Frame(self.graph_frame)
        self.graph_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 초기 그래프 생성
        self.fig = Figure(figsize=(10, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("실시간 센서 데이터")
        self.ax.set_xlabel("시간")
        self.ax.set_ylabel("값")
        self.ax.grid(True)
        
        # 캔버스에 그래프 추가
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_container)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 툴바 추가
        toolbar_frame = ttk.Frame(self.graph_container)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()
    
    def toggle_auto_update(self):
        """그래프 자동 업데이트 토글"""
        self.auto_update_graph = self.auto_update_var.get()
    
    def generate_test_data(self):
        """테스트용 더미 데이터 생성"""
        if not self.is_collecting:  # 실제 데이터 수집 중이 아닐 때만 테스트 데이터 생성
            # 더미 데이터 생성
            now = datetime.datetime.now()
            test_data = []
            
            for i in range(50):  # 50개 샘플 생성
                timestamp = now - datetime.timedelta(seconds=(50-i))
                data = {
                    "_timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                    "temperature": 25 + np.sin(i/10) * 5,
                    "humidity": 60 + np.cos(i/8) * 10,
                    "pressure": 1013 + np.sin(i/15) * 3,
                    "sample_time": i * 1000,
                    "device_id": "TEST_DEVICE",
                    "pt1": {
                        "value": 100 + np.sin(i/5) * 20,
                        "status": 1
                    },
                    "pt2": {
                        "value": 200 + np.cos(i/7) * 30,
                        "status": 1
                    }
                }
                test_data.append(data)
            
            # 데이터를 큐에 넣는 것처럼 처리
            self.all_data = test_data
            self.update_dataframe(test_data)
            self.update_data_table()
            self.update_statistics()
            
            # 컬럼 선택 자동화
            if hasattr(self, 'column_listbox'):
                self.column_listbox.selection_set(0, 3)  # 처음 4개 컬럼 선택
                self.update_graph_selection()
            
            # 상태 업데이트
            self.status_var.set(f"상태: 테스트 데이터 생성됨 ({len(test_data)}개)")
            
            # CSV 저장 버튼 활성화
            self.save_csv_button.config(state=tk.NORMAL)
    
    def setup_stats_view(self):
        """통계 데이터 표시 UI 설정"""
        # 통계 데이터 스크롤 영역
        stats_scroll = ttk.Frame(self.stats_frame)
        stats_scroll.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 캔버스와 스크롤바 설정
        canvas = tk.Canvas(stats_scroll)
        scrollbar = ttk.Scrollbar(stats_scroll, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 통계 내용 프레임
        self.stats_content = ttk.Frame(canvas)
        canvas_window = canvas.create_window((0, 0), window=self.stats_content, anchor="nw")
        
        # 스크롤바 연결
        def configure_scroll(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        self.stats_content.bind("<Configure>", configure_scroll)
        
        # 기본 메시지
        ttk.Label(self.stats_content, text="데이터 수집이 시작되면 통계가 여기에 표시됩니다.", 
                 font=('Arial', 12, 'italic')).pack(pady=20)
    
    def update_port_list(self):
        """시리얼 포트 목록 업데이트"""
        ports = list(serial.tools.list_ports.comports())
        port_list = [f"{port.device} - {port.description}" for port in ports]
        
        self.port_combobox['values'] = port_list
        if port_list:
            self.port_combobox.current(0)
            self.start_button.config(state=tk.NORMAL)
        else:
            self.status_var.set("상태: 사용 가능한 시리얼 포트가 없습니다.")
            self.start_button.config(state=tk.DISABLED)
    
    def start_collecting(self):
        """데이터 수집 시작"""
        if not self.port_combobox.get():
            messagebox.showwarning("경고", "시리얼 포트를 선택해주세요.")
            return
        
        try:
            # 포트 추출
            port = self.port_combobox.get().split(" - ")[0]
            baud_rate = int(self.baud_combobox.get())
            
            # 시리얼 포트 열기
            self.serial_port = serial.Serial(port, baud_rate, timeout=1)
            time.sleep(0.5)  # 시리얼 연결 안정화 대기
            
            # 상태 업데이트
            self.is_collecting = True
            self.stop_requested = False  # 새로운 플래그 추가
            self.status_var.set(f"상태: {port}에서 데이터 수집 중...")
            
            # 버튼 상태 변경
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.port_combobox.config(state=tk.DISABLED)
            self.baud_combobox.config(state=tk.DISABLED)
            
            # 수집 스레드 시작
            self.collect_thread = threading.Thread(target=self.collect_data, daemon=True)
            self.collect_thread.start()
            
            # UI 업데이트 시작
            self.root.after(UPDATE_INTERVAL, self.update_ui)
            
        except Exception as e:
            messagebox.showerror("오류", f"연결 오류: {str(e)}")
            self.status_var.set(f"상태: 연결 오류 - {str(e)}")
    
    def request_stop_collecting(self):
        """데이터 수집 중지 요청 - UI에서 호출되는 함수"""
        if self.is_collecting:
            self.stop_requested = True
            self.status_var.set("상태: 수집 중지 중...")
            self.stop_button.config(state=tk.DISABLED)  # 중복 클릭 방지
            # 중지 작업은 UI 스레드에서 별도로 진행
            self.root.after(100, self.check_stop_progress)
    
    def check_stop_progress(self):
        """수집 중지 진행 상태 확인"""
        if not self.is_collecting:
            # 이미 중지되었으면 UI 상태 업데이트
            self.update_ui_after_stop()
        else:
            # 아직 중지 중이면 계속 확인
            self.root.after(100, self.check_stop_progress)
    
    def update_ui_after_stop(self):
        """수집 중지 후 UI 상태 업데이트"""
        self.status_var.set(f"상태: 데이터 수집 중지됨. 총 {len(self.all_data)}개 수집됨")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.port_combobox.config(state="readonly")
        self.baud_combobox.config(state=tk.NORMAL)
    
    def collect_data(self):
        """별도 스레드에서 시리얼 데이터 수집"""
        self.serial_port.reset_input_buffer()
        
        while self.is_collecting and not getattr(self, 'stop_requested', False):
            try:
                if self.serial_port.in_waiting > 0:
                    line = self.serial_port.readline().decode('utf-8').strip()
                    if line.startswith("{") and line.endswith("}"):
                        try:
                            json_data = json.loads(line)
                            # 시간 정보 추가
                            json_data['_timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                            # 큐에 데이터 추가
                            self.data_queue.put(json_data)
                        except json.JSONDecodeError:
                            print(f"JSON 파싱 오류: {line}")
            except Exception as e:
                print(f"데이터 수집 오류: {e}")
                self.status_var.set(f"상태: 데이터 수집 오류 - {str(e)}")
                break
            
            time.sleep(0.01)  # CPU 사용량 최적화
        
        # 스레드 종료 전 시리얼 포트 닫기
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
            except:
                pass
            self.serial_port = None
        
        # 수집 중지 상태 설정
        self.is_collecting = False
    
    def update_ui(self):
        """UI 데이터 업데이트"""
        if not self.is_collecting:
            return
        
        # 큐에서 데이터 가져오기
        new_data = []
        while not self.data_queue.empty():
            new_data.append(self.data_queue.get())
        
        if new_data:
            # 전체 데이터에 추가
            self.all_data.extend(new_data)
            
            # 데이터프레임 업데이트
            self.update_dataframe(new_data)
            
            # 테이블 업데이트
            self.update_data_table()
            
            # 그래프 업데이트 (자동 업데이트가 활성화된 경우에만)
            if self.auto_update_graph and hasattr(self, 'selected_columns') and self.selected_columns:
                self.update_live_graph()
            
            # 통계 업데이트
            self.update_statistics()
            
            # 상태 바 업데이트
            self.status_var.set(f"상태: 데이터 수집 중... 총 {len(self.all_data)}개 수집됨")
            
            # CSV 저장 버튼 활성화
            if self.all_data and self.save_csv_button['state'] == tk.DISABLED:
                self.save_csv_button.config(state=tk.NORMAL)
        
        # 주기적으로 UI 업데이트
        self.root.after(UPDATE_INTERVAL, self.update_ui)
    
    def update_dataframe(self, new_data):
        """데이터프레임 업데이트"""
        # 새 데이터로 임시 데이터프레임 생성
        new_rows = []
        
        for data in new_data:
            # 기본 row 데이터 (timestamp 포함)
            row = {'timestamp': data.get('_timestamp', '')}
            
            # 첫 번째 레벨 키를 모두 추가 (pt1, pt2 제외)
            for key, value in data.items():
                if key != "pt1" and key != "pt2" and key != "_timestamp":
                    row[key] = value
            
            # pt1 데이터 추가 (있는 경우)
            if 'pt1' in data and isinstance(data['pt1'], dict):
                for key, value in data['pt1'].items():
                    row[f"pt1_{key}"] = value
            
            # pt2 데이터 추가 (있는 경우)
            if 'pt2' in data and isinstance(data['pt2'], dict):
                for key, value in data['pt2'].items():
                    row[f"pt2_{key}"] = value
            
            new_rows.append(row)
        
        # 새 데이터프레임 생성
        try:
            new_df = pd.DataFrame(new_rows)
            
            # 기존 데이터프레임과 합치기
            if self.df.empty:
                self.df = new_df
                
                # 첫 데이터가 들어오면 컬럼 리스트박스 업데이트
                self.update_column_list()
                
                # 초기 컬럼 자동 선택 (첫 4개)
                if self.column_listbox.size() > 0:
                    for i in range(min(4, self.column_listbox.size())):
                        self.column_listbox.selection_set(i)
                    self.update_graph_selection()
            else:
                self.df = pd.concat([self.df, new_df], ignore_index=True)
            
            # 최대 데이터 포인트 수 제한
            if len(self.df) > MAX_DATA_POINTS:
                self.df = self.df.iloc[-MAX_DATA_POINTS:]
        except Exception as e:
            print(f"데이터프레임 업데이트 오류: {e}")
    
    def update_column_list(self):
        """컬럼 리스트박스 업데이트"""
        if self.df.empty:
            return
        
        # 현재 리스트박스 내용 비우기
        self.column_listbox.delete(0, tk.END)
        
        # 수치형 열만 필터링
        numeric_cols = self.df.select_dtypes(include=np.number).columns.tolist()
        
        # 목록에 추가
        for col in numeric_cols:
            self.column_listbox.insert(tk.END, col)
    
    def update_data_table(self):
        """데이터 테이블 업데이트"""
        if self.df.empty:
            return
        
        try:
            # 현재 표시 중인 열 확인
            current_columns = self.data_table['columns']
            new_columns = list(self.df.columns)
            
            # 열이 변경된 경우 테이블 재구성
            if set(current_columns) != set(new_columns):
                # 기존 열 삭제
                self.data_table['columns'] = new_columns
                
                # 열 구성
                self.data_table.column('#0', width=50, stretch=tk.NO)
                for col in new_columns:
                    self.data_table.column(col, width=100)
                    self.data_table.heading(col, text=col)
                
                # 기존 데이터 삭제
                for i in self.data_table.get_children():
                    self.data_table.delete(i)
            
            # 표시할 최대 행 수
            max_rows = int(self.rows_spinbox.get())
            display_df = self.df.tail(max_rows)
            
            # 현재 행 수 확인
            current_rows = len(self.data_table.get_children())
            
            # 행이 변경된 경우에만 테이블 업데이트
            if current_rows != len(display_df):
                # 기존 행 삭제
                for i in self.data_table.get_children():
                    self.data_table.delete(i)
                
                # 새 행 추가
                for i, (_, row) in enumerate(display_df.iterrows()):
                    values = [row[col] for col in new_columns]
                    self.data_table.insert('', 'end', text=str(i+1), values=values)
                
                # 스크롤을 최하단으로 이동
                children = self.data_table.get_children()
                if children:
                    self.data_table.see(children[-1])
        except Exception as e:
            print(f"데이터 테이블 업데이트 오류: {e}")
    
    def update_graph_selection(self):
        """그래프에 표시할 열 선택 업데이트"""
        selection = self.column_listbox.curselection()
        if not selection:
            messagebox.showinfo("알림", "표시할 데이터 열을 하나 이상 선택해주세요.")
            return
        
        # 선택된 열 목록
        self.selected_columns = [self.column_listbox.get(i) for i in selection]
        
        try:
            # 그래프 초기화
            self.ax.clear()
            self.plot_data = {}
            
            # 타이틀 설정
            self.ax.set_title("실시간 센서 데이터")
            self.ax.set_xlabel("시간")
            self.ax.set_ylabel("값")
            self.ax.grid(True)
            
            # 그래프 업데이트
            self.update_live_graph()
        except Exception as e:
            print(f"그래프 선택 업데이트 오류: {e}")
    
    def update_live_graph(self):
        """실시간 그래프 업데이트"""
        if self.df.empty or not self.selected_columns:
            return
        
        try:
            # 그래프 초기화
            self.ax.clear()
            
            # 시간 데이터
            time_data = pd.to_datetime(self.df['timestamp'])
            
            # 각 선택된 열에 대해 그래프 그리기
            for column in self.selected_columns:
                if column in self.df.columns:
                    self.ax.plot(time_data, self.df[column], '-', label=column)
            
            # 그래프 설정
            self.ax.set_title("실시간 센서 데이터")
            self.ax.set_xlabel("시간")
            self.ax.set_ylabel("값")
            self.ax.grid(True)
            self.ax.legend(loc="upper left")
            
            # x축 날짜 포맷
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            self.fig.autofmt_xdate()
            
            # 캔버스 업데이트
            self.canvas.draw_idle()  # draw() 대신 draw_idle() 사용
        except Exception as e:
            print(f"그래프 업데이트 오류: {e}")
    
    def update_statistics(self):
        """통계 정보 업데이트"""
        if self.df.empty:
            return
        
        try:
            # 기존 내용 지우기
            for widget in self.stats_content.winfo_children():
                widget.destroy()
            
            # 데이터 요약 정보
            summary_frame = ttk.LabelFrame(self.stats_content, text="데이터 요약")
            summary_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Label(summary_frame, text=f"총 데이터 수: {len(self.all_data)}개").pack(anchor=tk.W, padx=10, pady=5)
            ttk.Label(summary_frame, text=f"수집 시작 시간: {self.df['timestamp'].iloc[0]}").pack(anchor=tk.W, padx=10, pady=2)
            ttk.Label(summary_frame, text=f"마지막 수집 시간: {self.df['timestamp'].iloc[-1]}").pack(anchor=tk.W, padx=10, pady=2)
            
            # 수치형 데이터 통계
            numeric_df = self.df.select_dtypes(include=np.number)
            
            if not numeric_df.empty:
                stats_frame = ttk.LabelFrame(self.stats_content, text="수치 데이터 통계")
                stats_frame.pack(fill=tk.X, padx=10, pady=10)
                
                # 통계 테이블
                stats_table = ttk.Treeview(stats_frame)
                stats_table.pack(fill=tk.X, padx=10, pady=10)
                
                # 열 설정
                stats_table['columns'] = ['mean', 'min', 'max', 'std']
                stats_table.column('#0', width=150, stretch=tk.NO)
                stats_table.column('mean', width=100, anchor=tk.E)
                stats_table.column('min', width=100, anchor=tk.E)
                stats_table.column('max', width=100, anchor=tk.E)
                stats_table.column('std', width=100, anchor=tk.E)
                
                stats_table.heading('#0', text='필드')
                stats_table.heading('mean', text='평균')
                stats_table.heading('min', text='최소값')
                stats_table.heading('max', text='최대값')
                stats_table.heading('std', text='표준편차')
                
                # 데이터 추가
                for column in numeric_df.columns:
                    values = numeric_df[column].dropna()
                    if len(values) > 0:
                        stats_table.insert('', 'end', text=column, values=(
                            f"{values.mean():.4g}",
                            f"{values.min():.4g}",
                            f"{values.max():.4g}",
                            f"{values.std():.4g}"
                        ))
        except Exception as e:
            print(f"통계 업데이트 오류: {e}")
    
    def stop_collecting(self):
        """데이터 수집 중지 (실제 중지 로직)"""
        self.is_collecting = False
        
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
            except:
                pass
            self.serial_port = None
        
        # UI 업데이트
        self.update_ui_after_stop()
    
    def save_to_csv(self):
        """수집된 데이터를 CSV 파일로 저장"""
        if self.df.empty:
            messagebox.showwarning("경고", "저장할 데이터가 없습니다.")
            return
        
        try:
            filename = f"duet_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            self.df.to_csv(filename, index=False)
            messagebox.showinfo("알림", f"데이터가 {filename}에 저장되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"파일 저장 중 오류 발생: {str(e)}")
    
    def on_closing(self):
        """프로그램 종료 시 처리"""
        if self.is_collecting:
            if messagebox.askyesno("종료 확인", "데이터 수집이 진행 중입니다. 종료하시겠습니까?"):
                self.stop_requested = True
                self.is_collecting = False
                if self.serial_port and self.serial_port.is_open:
                    try:
                        self.serial_port.close()
                    except:
                        pass
                self.root.destroy()
        else:
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = RealTimeDuetMonitor(root)
    root.mainloop() 