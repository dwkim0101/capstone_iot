"""
모드 선택 대화상자 모듈
"""
import tkinter as tk
from tkinter import ttk
import os
import traceback
import sys

# 디버깅 상수
DEBUG = True

def debug_print(*args, **kwargs):
    """디버깅 메시지 출력"""
    if DEBUG:
        print("[모드 선택기 디버그]", *args, **kwargs)
        sys.stdout.flush()  # 즉시 출력 반영

class ModeSelector(tk.Toplevel):
    def __init__(self, parent=None):
        """모드 선택 대화상자 초기화"""
        debug_print("ModeSelector 초기화 시작")
        try:
            super().__init__(parent)
            self.parent = parent
            self.title("DUET 모니터링 시스템 - 모드 선택")
            self.geometry("550x450")
            self.resizable(False, False)
            
            # 모달 대화상자로 설정
            self.transient(parent)
            self.grab_set()
            debug_print("모달 대화상자 설정 완료")
            
            # 포커스 설정
            self.focus_set()
            
            # 선택된 모드 (None: 취소, "full": 전체 모드, "lightweight": 경량 모드)
            self.selected_mode = None
            
            # UI 초기화
            self.setup_ui()
            debug_print("UI 초기화 완료")
            
            # 화면 중앙에 배치
            self.center_window()
            debug_print(f"화면 중앙 배치 완료: {self.geometry()}")
            
            # 항상 최상위로 표시
            self.attributes('-topmost', True)
            self.update()
            self.attributes('-topmost', False)
            
            # 대화상자가 닫힐 때까지 대기
            if parent:
                self.protocol("WM_DELETE_WINDOW", self.on_cancel)
                debug_print("대화상자 대기 시작")
                self.wait_window(self)
                debug_print("대화상자 대기 종료, 선택된 모드:", self.selected_mode)
        except Exception as e:
            debug_print(f"ModeSelector 초기화 오류: {e}")
            debug_print(traceback.format_exc())
            self.selected_mode = "full"  # 오류 발생 시 기본값 설정
        
    def setup_ui(self):
        """UI 초기화"""
        try:
            # 스타일 설정
            self.setup_style()
            
            # 메인 프레임
            main_frame = ttk.Frame(self, padding=20)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # 제목
            title_label = ttk.Label(
                main_frame, 
                text="DUET 모니터링 시스템 실행 모드 선택",
                font=("나눔고딕", 16, "bold"),
                style="Title.TLabel"
            )
            title_label.pack(pady=(0, 20))
            
            # 소개 텍스트
            intro_label = ttk.Label(
                main_frame,
                text="시스템 성능과 모니터링 용도에 맞는 실행 모드를 선택하세요.",
                font=("나눔고딕", 10),
                wraplength=500,
                justify=tk.CENTER
            )
            intro_label.pack(pady=(0, 20))
            
            # 모드 선택 프레임
            mode_frame = ttk.Frame(main_frame)
            mode_frame.pack(fill=tk.BOTH, expand=True)
            
            # 전체 모드 버튼
            full_frame = ttk.LabelFrame(mode_frame, text="전체 모드", style="Full.TLabelframe")
            full_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            full_title = ttk.Label(
                full_frame,
                text="고성능 모니터링",
                font=("나눔고딕", 12, "bold"),
                style="FullTitle.TLabel"
            )
            full_title.pack(pady=(10, 5), padx=10, anchor=tk.W)
            
            full_description = ttk.Label(
                full_frame,
                text=(
                    "모든 기능 사용 가능:\n\n"
                    "✓ 그래프 실시간 업데이트\n"
                    "✓ 데이터 테이블 및 통계 표시\n"
                    "✓ LED 디스플레이 시각화\n"
                    "✓ 포트 선택 및 상세 설정\n"
                    "✓ 데이터 저장 및 분석 기능\n\n"
                    "🖥️ 고성능 시스템 권장\n"
                    "🔄 데이터 처리량 많음"
                ),
                justify=tk.LEFT,
                wraplength=220
            )
            full_description.pack(pady=5, padx=10, anchor=tk.W)
            
            full_button = ttk.Button(
                full_frame,
                text="전체 모드로 시작",
                command=self.select_full_mode,
                width=20,
                style="Full.TButton"
            )
            full_button.pack(pady=(15, 15))
            
            # 경량 모드 버튼
            light_frame = ttk.LabelFrame(mode_frame, text="경량 모드", style="Light.TLabelframe")
            light_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            light_title = ttk.Label(
                light_frame,
                text="최소 리소스 모니터링",
                font=("나눔고딕", 12, "bold"),
                style="LightTitle.TLabel"
            )
            light_title.pack(pady=(10, 5), padx=10, anchor=tk.W)
            
            light_description = ttk.Label(
                light_frame,
                text=(
                    "필수 기능만 사용 가능:\n\n"
                    "✓ 그래프 간헐적 업데이트\n"
                    "✓ 필수 데이터만 저장\n"
                    "✓ 최소 메모리 사용\n"
                    "✓ 긴 업데이트 간격 (5초 이상)\n"
                    "✓ 시스템 부하 최소화\n\n"
                    "💻 저사양 시스템 최적화\n"
                    "⚡ 배터리 사용 효율적"
                ),
                justify=tk.LEFT,
                wraplength=220
            )
            light_description.pack(pady=5, padx=10, anchor=tk.W)
            
            light_button = ttk.Button(
                light_frame,
                text="경량 모드로 시작",
                command=self.select_lightweight_mode,
                width=20,
                style="Light.TButton"
            )
            light_button.pack(pady=(15, 15))
            
            # 취소 버튼
            cancel_button = ttk.Button(
                main_frame,
                text="취소",
                command=self.on_cancel,
                width=10
            )
            cancel_button.pack(pady=15)
        except Exception as e:
            debug_print(f"setup_ui 오류: {e}")
            debug_print(traceback.format_exc())
        
    def setup_style(self):
        """스타일 설정"""
        try:
            style = ttk.Style()
            
            # 제목 스타일
            style.configure("Title.TLabel", foreground="#1a237e", padding=10)
            
            # 전체 모드 스타일
            style.configure("Full.TLabelframe", borderwidth=2)
            style.configure("Full.TLabelframe.Label", foreground="#004d40", font=("나눔고딕", 12, "bold"))
            style.configure("FullTitle.TLabel", foreground="#004d40")
            style.configure("Full.TButton", foreground="#004d40")
            
            # 경량 모드 스타일
            style.configure("Light.TLabelframe", borderwidth=2)
            style.configure("Light.TLabelframe.Label", foreground="#0d47a1", font=("나눔고딕", 12, "bold"))
            style.configure("LightTitle.TLabel", foreground="#0d47a1")
            style.configure("Light.TButton", foreground="#0d47a1")
            debug_print("스타일 설정 완료")
        except Exception as e:
            debug_print(f"setup_style 오류: {e}")
            debug_print(traceback.format_exc())
        
    def center_window(self):
        """창을 화면 중앙에 배치"""
        try:
            self.update_idletasks()
            width = self.winfo_width()
            height = self.winfo_height()
            x = (self.winfo_screenwidth() // 2) - (width // 2)
            y = (self.winfo_screenheight() // 2) - (height // 2)
            self.geometry(f"{width}x{height}+{x}+{y}")
            debug_print(f"창 크기 조정: {width}x{height}, 위치: +{x}+{y}")
        except Exception as e:
            debug_print(f"center_window 오류: {e}")
            debug_print(traceback.format_exc())
        
    def select_full_mode(self):
        """전체 모드 선택"""
        debug_print("전체 모드 선택됨")
        self.selected_mode = "full"
        self.destroy()
        
    def select_lightweight_mode(self):
        """경량 모드 선택"""
        debug_print("경량 모드 선택됨")
        self.selected_mode = "lightweight"
        self.destroy()
        
    def on_cancel(self):
        """취소 버튼 클릭"""
        debug_print("모드 선택 취소됨")
        self.selected_mode = None
        self.destroy()
        
    def get_selected_mode(self):
        """선택된 모드 반환"""
        debug_print(f"선택된 모드 반환: {self.selected_mode}")
        return self.selected_mode
        
# 단독 실행 테스트용
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    app = ModeSelector(root)
    mode = app.get_selected_mode()
    print(f"선택된 모드: {mode}")
    root.destroy() 