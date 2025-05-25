"""
데이터 수집 제어 모듈
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import csv
from datetime import datetime
import time
from typing import Dict, Any, Callable
from ..core.serial_handler import SerialHandler
from ..core.csv_handler import CsvHandler
from ..core.data_processor import DataProcessor
from ..config.settings import DEFAULT_DATA_DIR, CSV_TIMESTAMP_FORMAT, DEFAULT_BAUD_RATE, DEFAULT_PORT

class DataControl(ttk.LabelFrame):
    def __init__(self, parent: tk.Widget, serial_handler: SerialHandler, 
                 csv_handler: CsvHandler, data_processor: DataProcessor,
                 start_callback: Callable = None, stop_callback: Callable = None):
        """
        데이터 수집 제어 초기화
        
        Args:
            parent: 부모 위젯
            serial_handler: 시리얼 통신 핸들러
            csv_handler: CSV 파일 핸들러
            data_processor: 데이터 처리기
            start_callback: 수집 시작 콜백
            stop_callback: 수집 종료 콜백
        """
        super().__init__(parent, text="데이터 수집 제어")
        self.parent = parent
        self.serial_handler = serial_handler
        self.csv_handler = csv_handler
        self.data_processor = data_processor
        self.start_callback = start_callback
        self.stop_callback = stop_callback
        
        # 상태 변수
        self.is_collecting = False
        self.is_lightweight_mode = False
        self.current_csv_path = None
        self.csv_file = None
        self.csv_writer = None
        self.last_update_time = 0
        self.update_count = 0
        
        # UI 초기화
        self.setup_ui()
        
    def setup_ui(self):
        """UI 초기화"""
        # 메인 프레임
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 상태 프레임
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 상태 레이블
        ttk.Label(status_frame, text="상태:").pack(side=tk.LEFT, padx=5)
        self.status_label = ttk.Label(status_frame, text="준비")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # 성능 모니터링 레이블
        self.perf_label = ttk.Label(status_frame, text="")
        self.perf_label.pack(side=tk.LEFT, padx=5)
        
        # 경량 모드 체크박스
        self.lightweight_var = tk.BooleanVar(value=False)
        self.lightweight_check = ttk.Checkbutton(
            status_frame, 
            text="경량 모드 (성능 최적화)", 
            variable=self.lightweight_var,
            command=self.toggle_lightweight_mode
        )
        self.lightweight_check.pack(side=tk.RIGHT, padx=5)
        
        # 업데이트 주기 설정 프레임
        update_frame = ttk.Frame(main_frame)
        update_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 업데이트 주기 레이블
        ttk.Label(update_frame, text="UI 업데이트 주기:").pack(side=tk.LEFT, padx=5)
        
        # 업데이트 주기 콤보박스
        self.update_interval_var = tk.StringVar(value="1초")
        self.update_interval_combo = ttk.Combobox(
            update_frame,
            textvariable=self.update_interval_var,
            values=["1초", "2초", "5초", "10초", "30초", "수동"],
            state="readonly",
            width=10
        )
        self.update_interval_combo.pack(side=tk.LEFT, padx=5)
        self.update_interval_combo.bind("<<ComboboxSelected>>", self.change_update_interval)
        
        # 업데이트 버튼
        self.update_button = ttk.Button(
            update_frame,
            text="지금 업데이트",
            command=self.manual_update,
            state=tk.DISABLED
        )
        self.update_button.pack(side=tk.RIGHT, padx=5)
        
        # 데이터 제한 설정 프레임
        limit_frame = ttk.Frame(main_frame)
        limit_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 데이터 제한 레이블
        ttk.Label(limit_frame, text="메모리 데이터 제한:").pack(side=tk.LEFT, padx=5)
        
        # 데이터 제한 콤보박스
        self.data_limit_var = tk.StringVar(value="최근 1000개")
        self.data_limit_combo = ttk.Combobox(
            limit_frame,
            textvariable=self.data_limit_var,
            values=["최근 100개", "최근 500개", "최근 1000개"],
            state="readonly",
            width=12
        )
        self.data_limit_combo.pack(side=tk.LEFT, padx=5)
        self.data_limit_combo.bind("<<ComboboxSelected>>", self.change_data_limit)
        
        # 데이터 수집 버튼 프레임
        collect_frame = ttk.Frame(main_frame)
        collect_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 시작 버튼
        self.start_button = ttk.Button(
            collect_frame, 
            text="데이터 수집 시작", 
            command=self.start_collection
        )
        self.start_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 중지 버튼
        self.stop_button = ttk.Button(
            collect_frame, 
            text="데이터 수집 중지", 
            command=self.stop_collection,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # CSV 파일 프레임
        csv_frame = ttk.Frame(main_frame)
        csv_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # CSV 저장 버튼
        self.save_button = ttk.Button(
            csv_frame,
            text="CSV 파일 저장",
            command=self.save_csv
        )
        self.save_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # CSV 로드 버튼
        self.load_button = ttk.Button(
            csv_frame,
            text="CSV 파일 로드",
            command=self.load_csv
        )
        self.load_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
    def toggle_lightweight_mode(self):
        """경량 모드 전환"""
        self.is_lightweight_mode = self.lightweight_var.get()
        
        if self.is_lightweight_mode:
            # 경량 모드 설정
            self.update_interval_var.set("5초")  # 더 긴 업데이트 간격
            self.data_limit_var.set("최근 500개")  # 더 적은 데이터 유지
            self.status_label.config(text="경량 모드 활성화")
            
            # 불필요한 UI 요소 숨기기
            self.update_interval_combo.config(state="disabled")
            self.data_limit_combo.config(state="disabled")
            self.update_button.config(state="disabled")
            
            # 데이터 프로세서 최적화
            if hasattr(self.data_processor, 'set_max_rows'):
                self.data_processor.set_max_rows(500)
                
            # 메인 윈도우에 경량 모드 알림
            if hasattr(self, 'parent') and hasattr(self.parent, 'master'):
                if hasattr(self.parent.master, 'set_lightweight_mode'):
                    self.parent.master.set_lightweight_mode(True)
        else:
            # 일반 모드로 복귀
            self.update_interval_var.set("1초")
            self.status_label.config(text="준비" if not self.is_collecting else "데이터 수집 중")
            
            # UI 요소 복원
            self.update_interval_combo.config(state="readonly")
            self.data_limit_combo.config(state="readonly")
            if self.update_interval_var.get() == "수동":
                self.update_button.config(state="normal")
                
            # 메인 윈도우에 일반 모드 알림
            if hasattr(self, 'parent') and hasattr(self.parent, 'master'):
                if hasattr(self.parent.master, 'set_lightweight_mode'):
                    self.parent.master.set_lightweight_mode(False)
        
        # 업데이트 간격 변경 적용
        self.change_update_interval()
        
        # 데이터 제한 변경 적용
        self.change_data_limit()
        
    def update_performance_info(self):
        """성능 정보 업데이트"""
        current_time = time.time()
        if self.last_update_time > 0:
            interval = current_time - self.last_update_time
            self.update_count += 1
            avg_interval = interval / self.update_count
            self.perf_label.config(text=f"평균 업데이트 간격: {avg_interval:.2f}초")
        self.last_update_time = current_time
        
    def change_update_interval(self, event=None):
        """UI 업데이트 주기 변경"""
        interval_text = self.update_interval_var.get()
        if interval_text == "수동":
            self.update_button.config(state=tk.NORMAL)
            ms = 0
        else:
            self.update_button.config(state=tk.DISABLED)
            if interval_text == "1초":
                ms = 1000
            elif interval_text == "2초":
                ms = 2000
            elif interval_text == "5초":
                ms = 5000
            elif interval_text == "10초":
                ms = 10000
            elif interval_text == "30초":
                ms = 30000
            else:
                ms = 1000
        if self.is_lightweight_mode and ms > 0:
            ms *= 2
        # MainWindow에 직접 set_update_interval 호출
        main_window = self.parent.master if hasattr(self.parent, 'master') else None
        if main_window and hasattr(main_window, 'set_update_interval'):
            main_window.set_update_interval(ms)
        
    def change_data_limit(self, event=None):
        """데이터 제한 변경"""
        limit_text = self.data_limit_var.get()
        if limit_text == "최근 100개":
            limit = 100
        elif limit_text == "최근 500개":
            limit = 500
        elif limit_text == "최근 1000개":
            limit = 1000
        else:
            limit = 0
        if hasattr(self, 'data_processor'):
            self.data_processor.set_max_rows(limit)
        # MainWindow에 직접 set_max_rows 호출(있으면)
        main_window = self.parent.master if hasattr(self.parent, 'master') else None
        if main_window and hasattr(main_window, 'data_processor') and hasattr(main_window.data_processor, 'set_max_rows'):
            main_window.data_processor.set_max_rows(limit)
        
    def manual_update(self):
        """수동 UI 업데이트 실행"""
        # 성능 정보 업데이트
        self.update_performance_info()
        
        # 메인 윈도우에 수동 업데이트 요청
        if hasattr(self, 'parent') and hasattr(self.parent, 'master'):
            if hasattr(self.parent.master, 'manual_update'):
                self.parent.master.manual_update()
    
    def start_collection(self):
        """데이터 수집 시작"""
        # 이미 수집 중이면 무시
        if self.is_collecting:
            return
        
        print("데이터 수집 시작 시도...")
        
        # 성능 모니터링 초기화
        self.last_update_time = time.time()
        self.update_count = 0
        
        # 시리얼 포트 연결 상태 확인
        print(f"시리얼 포트 연결 상태: {self.serial_handler.is_connected}")
        if not self.serial_handler.is_connected:
            # 시리얼 포트가 연결되어 있지 않으면 연결 시도
            try:
                # 포트 정보 가져오기 - 메인 윈도우의 포트 선택기 참조
                port_name = None
                baud_rate = DEFAULT_BAUD_RATE
                
                # 부모 위젯 탐색으로 메인 윈도우 참조
                parent = self.parent
                while parent and not hasattr(parent, 'port_selector'):
                    if hasattr(parent, 'master'):
                        parent = parent.master
                    else:
                        break
                
                # 포트 선택기 찾았으면 포트 정보 가져오기
                if hasattr(parent, 'port_selector'):
                    port_name = parent.port_selector.get_port()
                    baud_rate = parent.port_selector.get_baud_rate()
                
                # 포트 이름이 없으면 기본값 사용
                if not port_name:
                    port_name = DEFAULT_PORT
                
                # 시리얼 포트 연결
                if not self.serial_handler.connect(port_name, baud_rate):
                    messagebox.showerror("연결 오류", f"시리얼 포트({port_name})에 연결할 수 없습니다.")
                    return False
            except Exception as e:
                messagebox.showerror("연결 오류", f"시리얼 포트 연결 중 오류 발생: {e}")
                return False
        
        try:
            # CSV 파일 초기화
            current_time = datetime.now().strftime(CSV_TIMESTAMP_FORMAT)
            csv_path = os.path.join(DEFAULT_DATA_DIR, f"duet_data_{current_time}.csv")
            
            # 데이터 디렉토리 확인
            os.makedirs(DEFAULT_DATA_DIR, exist_ok=True)
            print(f"데이터 디렉토리 생성: {DEFAULT_DATA_DIR}")
            
            print(f"CSV 파일 경로: {csv_path}")
            print("CSV 파일 초기화 시도...")
            
            # CSV 파일 핸들러 설정
            if self.csv_handler:
                if not self.csv_handler.initialize(csv_path):
                    messagebox.showerror("파일 오류", f"CSV 파일({csv_path})을 초기화할 수 없습니다.")
                    return False
                print(f"CSV 파일 초기화됨: {csv_path}")
            
            # 데이터 프로세서 상태 초기화
            if self.data_processor:
                self.data_processor.clear_data()
            
            # 시리얼 핸들러에 콜백 함수 설정
            self.serial_handler.data_callback = self.data_received_callback
            
            # 시리얼 데이터 읽기 시작
            print("시리얼 데이터 읽기 시작 시도...")
            if not self.serial_handler.start_reading():
                messagebox.showerror("시리얼 오류", "시리얼 데이터 읽기를 시작할 수 없습니다.")
                return False
            print("시리얼 데이터 읽기 시작 성공")
            
            # 상태 업데이트
            self.is_collecting = True
            self.status_label.config(text="데이터 수집 중...")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            
            # 경량 모드 표시
            if self.is_lightweight_mode:
                print("경량 모드로 데이터 수집 시작")
            else:
                print("일반 모드로 데이터 수집 시작")
            
            # 콜백 함수 호출
            if self.start_callback:
                self.start_callback()
                print("시작 콜백 함수 호출")
            
            # 현재 CSV 파일 경로 저장
            self.current_csv_path = csv_path
            
            print("데이터 수집 시작 완료")
            return True
            
        except Exception as e:
            import traceback
            print(f"데이터 수집 시작 중 오류: {e}")
            print(traceback.format_exc())
            messagebox.showerror("오류", f"데이터 수집 시작 중 오류 발생:\n{e}")
            return False
            
    def stop_collection(self):
        """데이터 수집 중지"""
        try:
            # 시리얼 데이터 읽기 중지
            self.serial_handler.stop_reading()
            
            # 상태 업데이트
            self.is_collecting = False
            self.status_label.config(text="준비")
            
            # 버튼 상태 업데이트
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.save_button.config(state=tk.NORMAL)
            self.load_button.config(state=tk.NORMAL)
            
            # CSV 파일 닫기
            self.csv_handler.close()
            
            # 콜백 호출
            if self.stop_callback:
                self.stop_callback()
                
            return True
                
        except Exception as e:
            messagebox.showerror("데이터 수집 오류", f"데이터 수집 중지 중 오류 발생: {e}")
            return False
            
    def append_csv_data(self, data: Dict[str, Any]):
        """CSV 파일에 데이터 추가"""
        if not self.is_collecting or not self.csv_handler:
            return
            
        try:
            # 경량 모드에서는 메모리 사용 최소화
            if self.is_lightweight_mode:
                # 필수 데이터만 저장
                essential_data = {
                    'timestamp': data.get('timestamp'),
                    'type': data.get('type'),
                    'value': data.get('value')
                }
                self.csv_handler.append_data(essential_data)
            else:
                # 전체 데이터 저장
                self.csv_handler.append_data(data)
        except Exception as e:
            print(f"데이터 추가 중 오류: {e}")
            
    def save_csv(self):
        """CSV 파일 저장"""
        try:
            # 현재 데이터프레임 가져오기
            df = self.data_processor.get_dataframe()
            
            if df.empty:
                messagebox.showinfo("알림", "저장할 데이터가 없습니다.")
                return
            
            # 저장 경로 선택
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV 파일", "*.csv"), ("모든 파일", "*.*")],
                initialdir=DEFAULT_DATA_DIR,
                title="CSV 파일 저장"
            )
            
            if not file_path:
                return
            
            # CSV 저장
            success = self.csv_handler.save_dataframe(df, file_path)
            
            if success:
                messagebox.showinfo("성공", f"데이터가 성공적으로 저장되었습니다: {file_path}")
            else:
                messagebox.showerror("저장 실패", "데이터 저장 중 오류가 발생했습니다.")
                
        except Exception as e:
            messagebox.showerror("저장 오류", f"CSV 파일 저장 중 오류 발생: {e}")
            
    def load_csv(self):
        """CSV 파일 로드"""
        try:
            # 파일 경로 선택
            file_path = filedialog.askopenfilename(
                filetypes=[("CSV 파일", "*.csv"), ("모든 파일", "*.*")],
                initialdir=DEFAULT_DATA_DIR,
                title="CSV 파일 로드"
            )
            
            if not file_path:
                return
            
            # CSV 로드
            df = self.csv_handler.load_csv(file_path)
            
            if df is None or df.empty:
                messagebox.showerror("로드 실패", "CSV 파일을 로드할 수 없거나 비어 있습니다.")
                return
            
            # 데이터 프로세서에 업데이트
            if hasattr(self.data_processor, 'set_dataframe'):
                self.data_processor.set_dataframe(df)
                messagebox.showinfo("성공", f"데이터가 성공적으로 로드되었습니다: {len(df)}행")
            else:
                messagebox.showerror("기능 부재", "데이터 프로세서에 데이터프레임을 설정하는 메서드가 없습니다.")
                
        except Exception as e:
            messagebox.showerror("로드 오류", f"CSV 파일 로드 중 오류 발생: {e}")
            
    def data_received_callback(self, data: Dict[str, Any]):
        """
        시리얼 데이터 수신 콜백
        
        Args:
            data: 수신된 데이터
        """
        try:
            # 데이터 프로세서로 데이터 전달
            if self.data_processor:
                self.data_processor.update_dataframe(data)
                
            # CSV 파일에 데이터 추가
            self.append_csv_data(data)
            
            # 부모 윈도우의 콜백 함수 호출 (있으면)
            parent = self.parent
            while parent:
                if hasattr(parent, 'data_received_callback'):
                    parent.data_received_callback(data)
                    break
                if hasattr(parent, 'master'):
                    parent = parent.master
                else:
                    break
        except Exception as e:
            print(f"데이터 수신 콜백 처리 오류: {e}") 