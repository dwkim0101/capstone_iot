import json
import datetime
import pandas as pd
import numpy as np
import serial
import serial.tools.list_ports
import time
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import threading
import queue
import matplotlib.animation as animation
import matplotlib.dates as mdates
import matplotlib as mpl
import re

# 한글 폰트 문제 해결
mpl.rcParams['font.family'] = 'AppleGothic' if 'AppleGothic' in mpl.font_manager.get_font_names() else 'NanumGothic'
mpl.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

# 전역 상수
MAX_DATA_POINTS = 500  # 그래프에 표시할 최대 데이터 포인트 수
UPDATE_INTERVAL = 100  # 대시보드 업데이트 간격 (밀리초) - 빠른 업데이트를 위해 조정
DATA_BATCH_SIZE = 10  # 한번에 처리할 데이터 배치 크기

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
        
        # 4. LED 디스플레이 탭 (신규 추가)
        self.led_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.led_frame, text="LED 디스플레이")
        
        # LED 디스플레이 설정
        self.setup_led_display()
    
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
            # 즉시 중지 플래그 설정
            self.stop_requested = True
            self.is_collecting = False  # 즉시 수집 상태 변경
            self.status_var.set("상태: 수집 중지 중...")
            self.stop_button.config(state=tk.DISABLED)  # 중복 클릭 방지
            
            # 시리얼 포트 강제 종료
            if self.serial_port and self.serial_port.is_open:
                try:
                    self.serial_port.close()
                except:
                    pass
                self.serial_port = None
            
            # 즉시 UI 상태 업데이트
            self.update_ui_after_stop()
            
            # CSV 저장 버튼 활성화 (데이터가 있을 경우)
            if not self.df.empty:
                self.save_csv_button.config(state=tk.NORMAL)
    
    def update_ui_after_stop(self):
        """수집 중지 후 UI 상태 업데이트"""
        self.status_var.set(f"상태: 데이터 수집 중지됨. 총 {len(self.all_data)}개 수집됨")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.port_combobox.config(state="readonly")
        self.baud_combobox.config(state=tk.NORMAL)
    
    def collect_data(self):
        """
        시리얼 포트에서 데이터 수집 및 JSON 파싱 개선
        - 버퍼 관리 최적화
        - JSON 파싱 성능 향상
        - 데이터 수집 속도 개선
        """
        if not self.serial_port or not self.serial_port.is_open:
            print("시리얼 포트가 열려있지 않습니다.")
            return
        
        print(f"'{self.serial_port.port}'에서 데이터 수집 시작...")
        buffer = ""
        incomplete_json_start_time = None
        max_buffer_size = 10000  # 버퍼 최대 크기 제한
        
        # 수집 중단 플래그 초기화
        self.stop_collection = False
        self.is_collecting = True
        
        try:
            while self.is_collecting and not self.stop_collection and not getattr(self, 'stop_requested', False):
                # 시리얼 포트 체크
                if not self.serial_port or not self.serial_port.is_open:
                    print("시리얼 포트 연결이 끊어졌습니다.")
                    break
                
                # 시리얼 포트에서 데이터 읽기 (청크 단위로 읽기)
                if self.serial_port.in_waiting > 0:
                    chunk_size = min(self.serial_port.in_waiting, 1024)  # 최대 1KB씩 읽기
                    data = self.serial_port.read(chunk_size).decode('utf-8', errors='replace')
                    buffer += data
                    
                    # 버퍼 크기 제한 (메모리 관리)
                    if len(buffer) > max_buffer_size:
                        # 마지막 JSON 시작 위치부터만 유지
                        last_start = buffer.rfind('{')
                        if last_start > 0:
                            buffer = buffer[last_start:]
                            print(f"버퍼 크기 초과로 일부 잘림: {len(buffer)} 바이트")
                    
                    # 완전한 JSON 객체 찾기 (최적화된 방식)
                    while '{' in buffer and '}' in buffer:
                        start = buffer.find('{')
                        end = buffer.find('}', start) + 1
                        
                        if start >= 0 and end > start:
                            json_str = buffer[start:end]
                            buffer = buffer[end:]  # 처리된 JSON 제거
                            
                            try:
                                # JSON 파싱 (빠른 파싱)
                                json_data = json.loads(json_str)
                                
                                # 타임스탬프 추가 (최적화)
                                json_data['timestamp'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                                
                                # 데이터 큐에 추가
                                self.data_queue.put(json_data)
                                
                                # 불완전 JSON 타이머 초기화
                                incomplete_json_start_time = None
                                
                            except json.JSONDecodeError as e:
                                # 빠른 JSON 수정 시도
                                try:
                                    fixed_json, is_fixed, method, original_error = self.fix_json_string(json_str)
                                    if is_fixed:
                                        fixed_data = json.loads(fixed_json)
                                        fixed_data['_fixed'] = True
                                        fixed_data['_original_error'] = str(e)
                                        fixed_data['_recovery_method'] = method
                                        fixed_data['timestamp'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                                        
                                        # 수정된 데이터 큐에 추가
                                        self.data_queue.put(fixed_data)
                                except:
                                    pass  # 수정 실패 시 무시
                
                    # 불완전 JSON 처리 (타임아웃 기반)
                    if buffer and '{' in buffer and '}' not in buffer[buffer.find('{'):]:
                        if incomplete_json_start_time is None:
                            incomplete_json_start_time = time.time()
                    elif time.time() - incomplete_json_start_time > 1:  # 1초 타임아웃
                        # 불완전 JSON 제거
                        buffer = ""
                        incomplete_json_start_time = None
                
                # CPU 부하 감소를 위한 짧은 대기
                time.sleep(0.0001)  # 100마이크로초 대기
                
        except Exception as e:
            print(f"데이터 수집 오류: {e}")
            time.sleep(0.1)  # 오류 발생 시 잠시 대기
        
        finally:
            # 수집 종료 정리
            if self.serial_port and self.serial_port.is_open:
                try:
                    self.serial_port.close()
                    self.serial_port = None
                except:
                    pass
            
            # 상태 업데이트        
            self.is_collecting = False
            print("데이터 수집 종료")
    
    def update_ui(self):
        """UI 데이터 업데이트"""
        # 수집이 중지되었을 때 UI 정리
        if not self.is_collecting:
            # 이미 중지되었고 정리가 필요하면
            if getattr(self, 'stop_requested', False) and hasattr(self, 'save_csv_button'):
                self.update_ui_after_stop()
                self.stop_requested = False  # 플래그 초기화
            return
        
        try:
            # 큐에서 데이터 가져오기 (배치 처리로 성능 향상)
            new_data = []
            batch_count = 0
            
            try:
                while not self.data_queue.empty() and batch_count < DATA_BATCH_SIZE:
                    data_item = self.data_queue.get(block=False)
                    if data_item is not None:
                        new_data.append(data_item)
                        batch_count += 1
            except queue.Empty:
                # 큐가 비어있는 경우 무시
                pass
                
            if new_data:
                # 전체 데이터에 추가
                self.all_data.extend(new_data)
                
                # 데이터프레임 업데이트 (배치 처리)
                has_new_columns = self.update_dataframe(new_data)
                
                # 테이블 업데이트 (최적화)
                self.update_data_table()
                
                # 그래프 업데이트 (자동 업데이트가 활성화된 경우에만)
                if self.auto_update_graph and hasattr(self, 'selected_columns') and self.selected_columns:
                    # 새 데이터가 일정 수 이상이거나 새 컬럼이 추가되었을 때 그래프 갱신
                    if len(new_data) >= max(1, DATA_BATCH_SIZE // 2) or has_new_columns:
                        self.update_live_graph()
                
                # LED 디스플레이 업데이트 (필요한 경우)
                if hasattr(self, 'led_sensor_var') and self.led_sensor_var.get():
                    self.update_led_display()
                
                # 상태 바 업데이트
                self.status_var.set(f"상태: 데이터 수집 중... 총 {len(self.all_data)}개 수집됨 (최근 +{len(new_data)})")
                
                # 통계 업데이트 (최적화: 데이터 양이 많을 때는 간헐적으로 업데이트)
                if len(self.all_data) % 50 == 0 or len(self.all_data) < 50:
                    self.update_statistics()
                
                # CSV 저장 버튼 활성화
                if self.all_data and self.save_csv_button['state'] == tk.DISABLED:
                    self.save_csv_button.config(state=tk.NORMAL)
        except Exception as e:
            print(f"UI 업데이트 오류: {e}")
            import traceback
            traceback.print_exc()
        
        # 주기적으로 UI 업데이트
        self.root.after(UPDATE_INTERVAL, self.update_ui)
    
    def update_dataframe(self, data):
        """
        JSON 데이터를 DataFrame에 추가하는 함수 - 성능 최적화 버전
        """
        if not data:
            return False
        
        try:
            # 데이터가 리스트인지 확인
            if isinstance(data, list):
                # 배치 처리로 성능 향상
                new_rows = []
                all_new_columns = set()
                
                for item in data:
                    row, new_cols = self._process_data_item(item)
                    if row:
                        new_rows.append(row)
                        if new_cols:
                            all_new_columns.update(new_cols)
                
                if new_rows:
                    # 배치로 DataFrame에 추가
                    new_df = pd.DataFrame(new_rows)
                    if self.df.empty:
                        self.df = new_df
                    else:
                        # 컬럼 정렬 유지하면서 새 데이터 추가
                        self.df = pd.concat([self.df, new_df], ignore_index=True)
                        
                        # 최대 행 수 제한 (성능 최적화)
                        max_rows = 10000
                        if len(self.df) > max_rows:
                            self.df = self.df.iloc[-max_rows:]
                
                return bool(all_new_columns)
            else:
                # 단일 데이터 항목 처리
                row, new_cols = self._process_data_item(data)
                if row:
                    new_df = pd.DataFrame([row])
                    if self.df.empty:
                        self.df = new_df
                    else:
                        self.df = pd.concat([self.df, new_df], ignore_index=True)
                        
                        # 최대 행 수 제한
                        max_rows = 10000
                        if len(self.df) > max_rows:
                            self.df = self.df.iloc[-max_rows:]
                
                return bool(new_cols)
                
        except Exception as e:
            print(f"DataFrame 업데이트 오류: {e}")
            return False

    def _process_data_item(self, data):
        """단일 데이터 항목을 처리하여 행 데이터 반환"""
        if not data or not isinstance(data, dict):
            return None, None
        
        try:
            row = {}
            new_columns = set()
            
            # 타임스탬프 처리
            if 'timestamp' in data:
                row['timestamp'] = data['timestamp']
            
            # 기본 필드 추출 (제외할 키 외의 모든 값)
            exclude_keys = {'_fixed', '_original_error', '_recovery_method'}
            
            # 모든 최상위 키-값 쌍 처리 (중첩된 객체는 평탄화)
            for key, value in data.items():
                if key in exclude_keys:
                    continue
                    
                if isinstance(value, dict):
                    # 중첩된 객체(딕셔너리)를 평탄화
                    for sub_key, sub_value in value.items():
                        full_key = f"{key}_{sub_key}"
                        row[full_key] = sub_value
                        if full_key not in self.df.columns:
                            new_columns.add(full_key)
                else:
                    # 기본 키-값
                    row[key] = value
                    if key not in self.df.columns:
                        new_columns.add(key)
            
            return row, new_columns
                
        except Exception as e:
            print(f"데이터 항목 처리 오류: {e}")
            return None, None
    
    def update_column_list(self):
        """컬럼 리스트박스 업데이트"""
        if self.df.empty:
            return
        
        try:
            # 현재 리스트박스 내용 비우기
            self.column_listbox.delete(0, tk.END)
            
            # 수치형 열만 필터링
            numeric_cols = self.df.select_dtypes(include=np.number).columns.tolist()
            
            # 목록에 추가
            for col in numeric_cols:
                self.column_listbox.insert(tk.END, col)
            
            # LED 디스플레이 센서 목록도 업데이트
            current_selection = self.led_sensor_var.get()
            self.led_sensor_combo['values'] = numeric_cols
            
            # 선택 유지 또는 첫 항목 선택
            if current_selection in numeric_cols:
                self.led_sensor_var.set(current_selection)
            elif numeric_cols:
                self.led_sensor_var.set(numeric_cols[0])
                
        except Exception as e:
            print(f"컬럼 목록 업데이트 오류: {e}")
    
    def update_data_table(self):
        """데이터 테이블 업데이트 (성능 최적화)"""
        if self.df.empty:
            return
            
        try:
            # 테이블 데이터를 가져오기 전에 현재 스크롤 위치 저장
            current_scroll_y = self.data_table.yview()
            
            # 테이블 내용 삭제
            self.data_table.delete(*self.data_table.get_children())
            
            # 열 구성 확인 및 업데이트
            current_columns = self.data_table["columns"]
            new_columns = list(self.df.columns)
            
            # 열 목록이 변경된 경우에만 열 구성 업데이트
            if set(current_columns) != set(new_columns):
                # 기존 열 삭제
                for col in current_columns:
                    self.data_table.heading(col, text="")
                
                # 새 열 구성
                self.data_table["columns"] = new_columns
                
                # 열 너비와 정렬 설정
                for col in new_columns:
                    # 타임스탬프 컬럼 (넓게)
                    if col == 'timestamp':
                        self.data_table.column(col, width=150, anchor="w")
                    # 디버그 정보 컬럼 (중간)
                    elif col.startswith('_'):
                        self.data_table.column(col, width=100, anchor="center")
                    # 숫자 컬럼 (좁게)
                    elif any(col.startswith(p) for p in ['pt1_', 'pt2_']):
                        self.data_table.column(col, width=80, anchor="e")
                    # 나머지 컬럼 (중간)
                    else:
                        self.data_table.column(col, width=100, anchor="center")
                    
                    # 헤더 설정
                    header_text = col
                    self.data_table.heading(col, text=header_text)
            
            # 최대 표시 행 (성능 최적화)
            max_display_rows = 100  # 테이블에 최대 100행만 표시
            display_df = self.df.tail(max_display_rows)
            
            # DataFrame에서 데이터 가져와 테이블에 추가
            for idx, row in display_df.iterrows():
                values = [row.get(col, '') for col in new_columns]
                
                # 수정된 데이터는 특별한 스타일 적용 (더 가독성 좋은 배경색과 글자색)
                if row.get('_is_fixed_data', False):
                    item_id = self.data_table.insert('', 'end', values=values, text=str(idx + 1))  # 번호 추가
                    # 갈색 배경에 흰색 글씨 (다크모드에서 더 가독성 좋음)
                    self.data_table.item(item_id, tags=('fixed_data',))
                else:
                    self.data_table.insert('', 'end', values=values, text=str(idx + 1))  # 번호 추가
            
            # 수정된 행에 대한 스타일 설정
            self.data_table.tag_configure('fixed_data', background='#8B4513', foreground='white')
            
            # 스크롤 위치 복원 (사용자 경험 개선)
            if current_scroll_y and current_scroll_y[0] > 0:
                self.data_table.yview_moveto(current_scroll_y[0])
                
        except Exception as e:
            print(f"데이터 테이블 업데이트 오류: {e}")
            import traceback
            traceback.print_exc()
    
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
        """실시간 그래프 업데이트 - 성능 최적화 버전"""
        if self.df.empty or not self.selected_columns:
            return
        
        try:
            # 그래프 초기화
            self.ax.clear()
            
            # 데이터 샘플링 최적화
            df_len = len(self.df)
            if df_len > 200:
                # 표시할 최대 포인트 수 계산 (성능 최적화)
                max_points = 200
                sample_step = max(1, df_len // max_points)
                
                # 샘플링된 데이터프레임 생성
                display_df = self.df.iloc[::sample_step].copy()
                
                # 마지막 10개 데이터는 항상 포함 (최신 데이터 표시 보장)
                last_data = self.df.tail(10)
                display_df = pd.concat([display_df, last_data]).drop_duplicates()
                display_df = display_df.sort_index()
            else:
                display_df = self.df.copy()
            
            # 시간 데이터 처리 최적화
            if 'timestamp' in display_df.columns:
                time_data = pd.to_datetime(display_df['timestamp'])
            else:
                time_data = pd.date_range(
                    start=datetime.datetime.now() - datetime.timedelta(seconds=len(display_df)),
                    periods=len(display_df),
                    freq='S'
                )
            
            # 그래프 스타일 설정 (한 번만)
            self.ax.grid(True, alpha=0.3)
            self.ax.set_title("실시간 센서 데이터")
            self.ax.set_xlabel("시간")
            self.ax.set_ylabel("값")
            
            # x축 포맷 설정 (한 번만)
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            for label in self.ax.get_xticklabels():
                label.set_rotation(30)
                label.set_ha('right')
            
            # 각 선택된 열에 대해 그래프 그리기 (최적화)
            for column in self.selected_columns:
                if column in display_df.columns:
                    # NaN 값 없는 서브셋만 플롯
                    valid_data = display_df[~display_df[column].isna()]
                    if not valid_data.empty:
                        if 'timestamp' in valid_data.columns:
                            valid_times = pd.to_datetime(valid_data['timestamp'])
                        else:
                            valid_indices = valid_data.index
                            valid_times = [time_data[i] for i in valid_indices if i < len(time_data)]
                        
                        if len(valid_times) > 0:
                            # 데이터 유형에 따른 색상 및 레이블 설정
                            if 'pt1_' in column:
                                color = 'blue'
                                label = f"{column} (센서1)"
                            elif 'pt2_' in column:
                                color = 'red'
                                label = f"{column} (센서2)"
                            else:
                                color = None
                                label = column
                            
                            # 그래프 그리기 (선 두께 최적화)
                            self.ax.plot(valid_times, valid_data[column], '-',
                                       label=label, linewidth=1.0, color=color)
            
            # 범례 설정 (한 번만)
            if self.selected_columns:
                self.ax.legend(loc="upper left", fontsize='small')
                self.ax.autoscale(enable=True, axis='y')
            
            # 캔버스 업데이트 (최적화)
            self.canvas.draw_idle()
        
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
        """수집된 데이터를 CSV 파일로 저장 (안정성 개선)"""
        if self.df.empty:
            messagebox.showwarning("경고", "저장할 데이터가 없습니다.")
            return
        
        try:
            # 현재 데이터프레임 복사 (작업 중 변경 방지)
            save_df = self.df.copy()
            
            # 파일명 설정 (현재 시간 기준)
            default_filename = f"duet_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            # 파일 저장 대화상자
            filename = filedialog.asksaveasfilename(
                title="CSV 파일 저장",
                defaultextension=".csv",
                initialfile=default_filename,
                filetypes=[("CSV 파일", "*.csv"), ("모든 파일", "*.*")]
            )
            
            if filename:
                # 저장 중 UI 상태 표시
                original_status = self.status_var.get()
                self.status_var.set(f"CSV 파일 저장 중...")
                self.root.update_idletasks()  # UI 즉시 업데이트
                
                # 파일 저장
                save_df.to_csv(filename, index=False)
                
                # 성공 메시지
                self.status_var.set(f"CSV 파일이 저장되었습니다: {filename}")
                messagebox.showinfo("저장 완료", f"데이터가 {filename}에 저장되었습니다.\n총 {len(save_df)}개 레코드")
                
                # 원래 상태로 복원
                self.root.after(3000, lambda: self.status_var.set(original_status))
        
        except Exception as e:
            error_msg = str(e)
            print(f"CSV 저장 오류: {error_msg}")
            messagebox.showerror("오류", f"파일 저장 중 오류 발생:\n{error_msg}")
            self.status_var.set(f"CSV 저장 오류 발생")
    
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

    def setup_led_display(self):
        """LED 디스플레이 UI 설정"""
        # 컨트롤 프레임
        led_control = ttk.Frame(self.led_frame)
        led_control.pack(fill=tk.X, padx=5, pady=5)
        
        # 표시할 데이터 선택 프레임
        select_frame = ttk.LabelFrame(led_control, text="표시할 데이터 선택")
        select_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        # 센서 선택
        ttk.Label(select_frame, text="센서 값:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.led_sensor_var = tk.StringVar()
        self.led_sensor_combo = ttk.Combobox(select_frame, textvariable=self.led_sensor_var, state="readonly", width=15)
        self.led_sensor_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # 디스플레이 갱신 주기
        ttk.Label(select_frame, text="갱신 주기(ms):").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.led_update_ms = tk.StringVar(value="1000")
        update_entry = ttk.Entry(select_frame, textvariable=self.led_update_ms, width=5)
        update_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # 디스플레이 스타일 프레임
        style_frame = ttk.LabelFrame(led_control, text="디스플레이 스타일")
        style_frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 색상 선택
        ttk.Label(style_frame, text="LED 색상:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.led_color_var = tk.StringVar(value="red")
        color_combo = ttk.Combobox(style_frame, textvariable=self.led_color_var, state="readonly", width=8,
                                 values=["red", "green", "blue", "orange", "purple"])
        color_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # LED 크기 선택
        ttk.Label(style_frame, text="LED 크기:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.led_size_var = tk.IntVar(value=30)
        size_combo = ttk.Combobox(style_frame, textvariable=self.led_size_var, state="readonly", width=5,
                                values=[20, 30, 40, 50])
        size_combo.grid(row=0, column=3, padx=5, pady=5)
        
        # LED 디스플레이 캔버스
        display_frame = ttk.Frame(self.led_frame)
        display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # LED 디스플레이 캔버스 생성
        self.led_canvas = tk.Canvas(display_frame, bg='black', highlightthickness=0)
        self.led_canvas.pack(fill=tk.BOTH, expand=True)
        
        # LED 디스플레이 초기화
        self.led_segments = []  # 7-세그먼트 디스플레이의 세그먼트 ID 저장
        self.led_dots = []      # 소수점 저장
        self.led_update_id = None  # 업데이트 ID
        
        # 초기 LED 디스플레이 생성
        self.create_led_display()
        
        # 값이 선택되면 자동으로 업데이트 시작
        def on_sensor_selected(event):
            self.start_led_update()
        
        self.led_sensor_combo.bind("<<ComboboxSelected>>", on_sensor_selected)
        
        # 색상이나 크기가 변경되면 디스플레이 업데이트
        self.led_color_var.trace_add("write", lambda *args: self.update_led_style())
        self.led_size_var.trace_add("write", lambda *args: self.create_led_display())
    
    def create_led_display(self):
        """7-세그먼트 LED 디스플레이 생성"""
        # 기존 LED 삭제
        self.led_canvas.delete("all")
        self.led_segments = []
        self.led_dots = []
        
        # LED 크기 및 간격 설정
        led_size = self.led_size_var.get()
        segment_width = led_size // 5
        segment_length = led_size * 2
        segment_gap = led_size // 10
        digit_gap = led_size
        
        # 디지털 시계 스타일 7-세그먼트 디스플레이 생성 (8자리)
        for digit in range(8):
            x_offset = 50 + digit * (segment_length + digit_gap)
            y_offset = 100
            
            # 각 디지트의 7개 세그먼트 (a, b, c, d, e, f, g)
            segments = []
            
            # a: 상단 가로
            a = self.led_canvas.create_rectangle(
                x_offset, y_offset,
                x_offset + segment_length, y_offset + segment_width,
                fill='gray20', outline='', tags=f'digit{digit}_a'
            )
            segments.append(a)
            
            # b: 우상단 세로
            b = self.led_canvas.create_rectangle(
                x_offset + segment_length - segment_width, y_offset,
                x_offset + segment_length, y_offset + segment_length,
                fill='gray20', outline='', tags=f'digit{digit}_b'
            )
            segments.append(b)
            
            # c: 우하단 세로
            c = self.led_canvas.create_rectangle(
                x_offset + segment_length - segment_width, y_offset + segment_length,
                x_offset + segment_length, y_offset + segment_length * 2,
                fill='gray20', outline='', tags=f'digit{digit}_c'
            )
            segments.append(c)
            
            # d: 하단 가로
            d = self.led_canvas.create_rectangle(
                x_offset, y_offset + segment_length * 2 - segment_width,
                x_offset + segment_length, y_offset + segment_length * 2,
                fill='gray20', outline='', tags=f'digit{digit}_d'
            )
            segments.append(d)
            
            # e: 좌하단 세로
            e = self.led_canvas.create_rectangle(
                x_offset, y_offset + segment_length,
                x_offset + segment_width, y_offset + segment_length * 2,
                fill='gray20', outline='', tags=f'digit{digit}_e'
            )
            segments.append(e)
            
            # f: 좌상단 세로
            f = self.led_canvas.create_rectangle(
                x_offset, y_offset,
                x_offset + segment_width, y_offset + segment_length,
                fill='gray20', outline='', tags=f'digit{digit}_f'
            )
            segments.append(f)
            
            # g: 중앙 가로
            g = self.led_canvas.create_rectangle(
                x_offset, y_offset + segment_length - segment_width // 2,
                x_offset + segment_length, y_offset + segment_length + segment_width // 2,
                fill='gray20', outline='', tags=f'digit{digit}_g'
            )
            segments.append(g)
            
            # 소수점
            if digit < 7:  # 마지막 자리 뒤에는 소수점 없음
                dot = self.led_canvas.create_oval(
                    x_offset + segment_length + segment_gap, 
                    y_offset + segment_length * 2 - segment_width,
                    x_offset + segment_length + segment_gap + segment_width,
                    y_offset + segment_length * 2,
                    fill='gray20', outline='', tags=f'digit{digit}_dot'
                )
                self.led_dots.append(dot)
            
            self.led_segments.append(segments)
        
        # 단위 표시 (°C, % 등)
        unit_x = 50 + 8 * (segment_length + digit_gap)
        self.unit_text = self.led_canvas.create_text(
            unit_x, 100 + segment_length,
            text="", fill=self.led_color_var.get(), font=('Arial', led_size // 2),
            tags='unit_text'
        )
        
        # 레이블 표시
        self.sensor_label = self.led_canvas.create_text(
            50, 50, text="센서 데이터", fill='white', font=('Arial', led_size // 2),
            anchor='w', tags='sensor_label'
        )
    
    def update_led_style(self):
        """LED 디스플레이 스타일 업데이트"""
        color = self.led_color_var.get()
        
        # 켜진 세그먼트의 색상 변경
        for digit in range(len(self.led_segments)):
            for i, segment in enumerate(self.led_segments[digit]):
                if self.led_canvas.itemcget(segment, 'fill') != 'gray20':
                    self.led_canvas.itemconfig(segment, fill=color)
        
        # 켜진 소수점의 색상 변경
        for dot in self.led_dots:
            if self.led_canvas.itemcget(dot, 'fill') != 'gray20':
                self.led_canvas.itemconfig(dot, fill=color)
        
        # 단위 텍스트 색상 변경
        self.led_canvas.itemconfig(self.unit_text, fill=color)
    
    def display_digit(self, position, digit, with_dot=False):
        """특정 위치에 숫자 표시"""
        if position < 0 or position >= len(self.led_segments):
            return
            
        # 7-세그먼트 표시를 위한 패턴 정의
        # 각 숫자별로 켜야할 세그먼트 인덱스 (a,b,c,d,e,f,g)
        patterns = {
            0: [0, 1, 2, 3, 4, 5],    # 0: a,b,c,d,e,f
            1: [1, 2],                # 1: b,c
            2: [0, 1, 3, 4, 6],       # 2: a,b,d,e,g
            3: [0, 1, 2, 3, 6],       # 3: a,b,c,d,g
            4: [1, 2, 5, 6],          # 4: b,c,f,g
            5: [0, 2, 3, 5, 6],       # 5: a,c,d,f,g
            6: [0, 2, 3, 4, 5, 6],    # 6: a,c,d,e,f,g
            7: [0, 1, 2],             # 7: a,b,c
            8: [0, 1, 2, 3, 4, 5, 6], # 8: a,b,c,d,e,f,g
            9: [0, 1, 2, 3, 5, 6],    # 9: a,b,c,d,f,g
            '-': [6],                 # -: g
            ' ': [],                  # 공백: 없음
            'E': [0, 3, 4, 5, 6],     # E: a,d,e,f,g
            'r': [6, 4],              # r: g,e
            'o': [2, 3, 4, 6],        # o: c,d,e,g
            'r': [6],                 # r: g
        }
        
        # 숫자를 문자열로 변환하고 범위 검사
        if isinstance(digit, (int, float)):
            digit_str = str(int(digit))
            if len(digit_str) > 1:
                digit_str = digit_str[-1]  # 마지막 자리만 사용
        else:
            digit_str = str(digit)[0]  # 첫 문자만 사용
        
        # 패턴 가져오기
        if digit_str in '0123456789- ':
            pattern = patterns.get(digit_str if digit_str == ' ' else int(digit_str) if digit_str.isdigit() else digit_str, [])
        else:
            pattern = patterns.get(digit_str, [])  # 특수 문자 (E, r, o 등)
        
        # 모든 세그먼트 끄기
        for i, segment in enumerate(self.led_segments[position]):
            self.led_canvas.itemconfig(segment, fill='gray20')
        
        # 해당 패턴의 세그먼트 켜기
        color = self.led_color_var.get()
        for i in pattern:
            self.led_canvas.itemconfig(self.led_segments[position][i], fill=color)
        
        # 소수점 표시 (마지막 자리는 제외)
        if position < len(self.led_dots):
            dot_color = color if with_dot else 'gray20'
            self.led_canvas.itemconfig(self.led_dots[position], fill=dot_color)
    
    def display_value(self, value, unit=""):
        """LED 디스플레이에 값 표시"""
        if value is None:
            # 에러 표시 (Error)
            for i in range(8):
                if i == 0:
                    self.display_digit(i, 'E')
                elif i == 1:
                    self.display_digit(i, 'r')
                elif i == 2:
                    self.display_digit(i, 'r')
                elif i == 3:
                    self.display_digit(i, 'o')
                elif i == 4:
                    self.display_digit(i, 'r')
                else:
                    self.display_digit(i, ' ')
            return
            
        # 값을 문자열로 변환하고 필요한 경우 반올림
        if isinstance(value, (int, float)):
            # 소수점 자릿수에 따라 반올림 및 포맷팅
            if abs(value) >= 10000:
                # 너무 큰 값은 지수 표기법으로
                value_str = f"{value:.2e}"
            elif abs(value) >= 1000:
                # 천 단위는 정수로
                value_str = f"{int(value):d}"
            elif abs(value) >= 100:
                # 백 단위는 소수점 1자리
                value_str = f"{value:.1f}"
            else:
                # 작은 값은 소수점 2자리
                value_str = f"{value:.2f}"
        else:
            value_str = str(value)
        
        # LED 디스플레이에 맞게 문자열 조정 (최대 8자리)
        if len(value_str) > 8:
            value_str = value_str[:8]  # 앞 8자리만 표시
        
        # 오른쪽 정렬하면서 앞에 빈칸 추가
        value_str = value_str.rjust(8)
        
        # 각 자리 표시
        for i in range(8):
            if i < len(value_str):
                char = value_str[i]
                # 소수점 여부 확인
                with_dot = False
                if i + 1 < len(value_str) and value_str[i + 1] == '.':
                    with_dot = True
                    value_str = value_str[:i+1] + value_str[i+2:]  # 소수점 제거
                
                self.display_digit(i, char, with_dot)
            else:
                self.display_digit(i, ' ')  # 빈칸
        
        # 단위 표시
        self.led_canvas.itemconfig(self.unit_text, text=unit)
        
        # 센서 레이블 업데이트
        sensor_name = self.led_sensor_var.get()
        self.led_canvas.itemconfig(self.sensor_label, text=f"{sensor_name} 센서 데이터")
    
    def start_led_update(self):
        """LED 디스플레이 업데이트 시작"""
        # 이전 업데이트 취소
        if self.led_update_id:
            self.root.after_cancel(self.led_update_id)
            self.led_update_id = None
        
        # 센서가 선택되지 않았으면 중지
        sensor = self.led_sensor_var.get()
        if not sensor:
            return
        
        # 업데이트 주기 확인
        try:
            update_ms = int(self.led_update_ms.get())
            if update_ms < 100:
                update_ms = 100  # 최소 100ms
        except:
            update_ms = 1000  # 기본값
            
        self.update_led_display()
        
        # 주기적인 업데이트 예약
        self.led_update_id = self.root.after(update_ms, self.start_led_update)
    
    def update_led_display(self):
        """LED 디스플레이 데이터 업데이트 - 숫자형 데이터가 없는 경우에도 동작하도록 개선"""
        sensor = self.led_sensor_var.get()
        if not sensor or self.df.empty:
            # 선택된 센서가 없거나 데이터프레임이 비어있으면 에러 표시
            self.display_value(None, "")
            return
            
        try:
            # 최신 데이터 가져오기
            latest_value = None
            unit = ""
            
            # 데이터프레임에 선택된 센서 컬럼이 있는지 확인
            if sensor in self.df.columns:
                # 마지막 행에서 센서 값 가져오기
                last_row = self.df.iloc[-1]
                if pd.notna(last_row[sensor]):  # NaN이 아닌 경우에만 사용
                    latest_value = last_row[sensor]
                
                # 단위 추정
                if "temperature" in sensor.lower():
                    unit = "°C"
                elif "humidity" in sensor.lower():
                    unit = "%"
                elif "pressure" in sensor.lower():
                    unit = "hPa"
                elif "pm" in sensor.lower() or "particle" in sensor.lower():
                    unit = "μg/m³"
                elif "voltage" in sensor.lower():
                    unit = "V"
                elif "current" in sensor.lower():
                    unit = "A"
                    
            # 유효한 값이 없으면 이전 행들에서 찾아보기 (최대 10개 이전 행까지)
            if latest_value is None and len(self.df) > 1:
                for i in range(min(10, len(self.df))):
                    idx = -1 - i  # 마지막 행부터 역순으로
                    if sensor in self.df.columns and pd.notna(self.df.iloc[idx][sensor]):
                        latest_value = self.df.iloc[idx][sensor]
                        print(f"이전 행({i+1}번째 이전)에서 유효한 '{sensor}' 값 찾음: {latest_value}")
                        break
            
            # 그래도 값이 없으면 다른 컬럼 중에서 유사한 이름의 컬럼 찾기
            if latest_value is None:
                # 유사한 컬럼 찾기 (예: pt1_pm10_standard 대신 pm10_standard 시도)
                alt_sensor = None
                
                # pt1_ 접두사 제거해서 시도
                if sensor.startswith('pt1_'):
                    alt_sensor = sensor[4:]  # 'pt1_' 제거
                    
                # 반대로 pt1_ 접두사 추가해서 시도    
                elif 'pt1_' + sensor in self.df.columns:
                    alt_sensor = 'pt1_' + sensor
                
                # 대체 센서가 있으면 해당 값 사용
                if alt_sensor and alt_sensor in self.df.columns and pd.notna(self.df.iloc[-1][alt_sensor]):
                    latest_value = self.df.iloc[-1][alt_sensor]
                    print(f"대체 센서 '{alt_sensor}'에서 값 찾음: {latest_value}")
            
            # LED 디스플레이에 값 표시 (값이 없으면 에러 표시)
            self.display_value(latest_value, unit)
            
        except Exception as e:
            print(f"LED 디스플레이 업데이트 오류: {e}")
            import traceback
            traceback.print_exc()
            self.display_value(None, "")  # 에러 표시
    
    def fix_json_string(self, json_str):
        """
        불완전하거나 손상된 JSON 문자열을 복구하는 함수
        여러 복구 전략을 시도하고 성공 여부를 반환합니다.
        """
        original_str = json_str
        is_fixed = False
        method = "none"
        original_error = ""
        
        # 이미 유효한 JSON인지 확인
        try:
            json.loads(json_str)
            return json_str, False, "already_valid", ""
        except json.JSONDecodeError as e:
            original_error = str(e)
            
        try:
            # 전략 1: 불균형 중괄호 수정
            open_braces = json_str.count('{')
            close_braces = json_str.count('}')
            
            if open_braces > close_braces:
                # 닫는 중괄호 추가
                json_str = json_str + '}' * (open_braces - close_braces)
                method = "added_closing_braces"
                is_fixed = True
                print(f"JSON 수정: 닫는 중괄호 {open_braces - close_braces}개 추가")
            elif close_braces > open_braces:
                # 여는 중괄호 추가
                json_str = '{' * (close_braces - open_braces) + json_str
                method = "added_opening_braces"
                is_fixed = True
                print(f"JSON 수정: 여는 중괄호 {close_braces - open_braces}개 추가")
                
            # 전략 2: 따옴표 문제 수정
            quote_count = json_str.count('"')
            if quote_count % 2 != 0:
                # 홀수 개의 따옴표 - 마지막에 닫는 따옴표 추가
                json_str = json_str + '"'
                method += "_fixed_quotes"
                is_fixed = True
                print("JSON 수정: 닫는 따옴표 추가")
                
            # 전략 3: 쉼표 문제 수정
            if ",," in json_str:
                json_str = json_str.replace(",,", ",")
                method += "_fixed_commas"
                is_fixed = True
                print("JSON 수정: 중복 쉼표 제거")
                
            if json_str.endswith(",}"):
                json_str = json_str[:-2] + "}"
                method += "_fixed_trailing_comma"
                is_fixed = True
                print("JSON 수정: 마지막 쉼표 제거")
                
            # 수정된 JSON 유효성 검사
            if is_fixed:
                try:
                    json.loads(json_str)
                    print(f"JSON 수정 성공: {method}")
                    return json_str, True, method, original_error
                except json.JSONDecodeError as e:
                    # 첫 번째 수정 시도 실패
                    print(f"첫 번째 수정 실패: {e}")
                    
            # 전략 4: 키-값 쌍 구조 추정 복구
            if '"' in json_str:
                try:
                    # 중괄호 확인
                    if not json_str.startswith('{'): 
                        json_str = '{' + json_str
                        method += "_added_opening_brace"
                    if not json_str.endswith('}'): 
                        json_str = json_str + '}'
                        method += "_added_closing_brace"
                    
                    # 키-값 구조 확인
                    parts = json_str[1:-1].split(',')
                    reconstructed_parts = []
                    
                    for part in parts:
                        if part.strip():
                            if ':' not in part:
                                # 키-값 구분자 없음
                                continue
                            
                            key_value = part.split(':', 1)
                            key = key_value[0].strip()
                            value = key_value[1].strip() if len(key_value) > 1 else ""
                            
                            # 키에 따옴표 추가
                            if not (key.startswith('"') and key.endswith('"')):
                                key = f'"{key.strip("\"")}"'
                                
                            # 숫자가 아닌 값에 따옴표 추가
                            if value and not value.startswith('"') and not value.endswith('"'):
                                try:
                                    float(value)  # 숫자인지 확인
                                except ValueError:
                                    # 이미 객체나 배열이 아닌 경우 따옴표 추가
                                    if not (value.startswith('{') or value.startswith('[')):
                                        value = f'"{value.strip("\"")}"'
                            
                            reconstructed_parts.append(f"{key}:{value}")
                    
                    # 재구성된 JSON
                    reconstructed_json = '{' + ','.join(reconstructed_parts) + '}'
                    
                    # 유효성 검사
                    json.loads(reconstructed_json)
                    method += "_key_value_reconstruction"
                    print(f"JSON 키-값 구조 재구성 성공")
                    return reconstructed_json, True, method, original_error
                    
                except Exception as reconstruction_error:
                    print(f"구조 재구성 실패: {reconstruction_error}")
            
            # 모든 수정 시도 실패
            return original_str, False, "no_valid_fix", original_error
            
        except Exception as error:
            print(f"JSON 수정 중 오류 발생: {error}")
            return original_str, False, "error_during_fix", original_error


if __name__ == "__main__":
    root = tk.Tk()
    app = RealTimeDuetMonitor(root)
    root.mainloop() 