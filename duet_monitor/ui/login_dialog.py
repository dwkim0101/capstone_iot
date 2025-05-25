import tkinter as tk
from tkinter import ttk, messagebox
import requests
from duet_monitor.config.api_config import LOGIN_URL, SIGNUP_URL
from duet_monitor.utils.debug import debug_print_main

WINDOW_BG = '#2d2d2d'

class SignupDialog(tk.Toplevel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.title("회원가입")
        self.geometry("400x320")
        self.resizable(False, False)
        self.result = None
        self.setup_ui()
        self.grab_set()
        self.focus_set()
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.wait_window(self)

    def setup_ui(self):
        frame = tk.Frame(self, bg=WINDOW_BG)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 한글 입력 방지 함수
        def no_korean_input(P):
            import re
            # 한글 유니코드 범위: \uac00-\ud7a3
            return not bool(re.search(r"[\uac00-\ud7a3]", P))
        vcmd = (self.register(no_korean_input), '%P')

        tk.Label(frame, text="이메일:", bg=WINDOW_BG, fg="white", font=("나눔고딕", 12, "bold")).pack(anchor=tk.W, pady=(0,2))
        self.email_entry = tk.Entry(frame, width=30, font=("나눔고딕", 12),
                                   validate="key", validatecommand=vcmd)
        self.email_entry.pack(pady=(0,10))
        self.email_entry.bind('<KeyRelease>', lambda e: self._remove_korean(self.email_entry))

        tk.Label(frame, text="비밀번호:", bg=WINDOW_BG, fg="white", font=("나눔고딕", 12, "bold")).pack(anchor=tk.W, pady=(0,2))
        self.password_entry = tk.Entry(frame, show="*", width=30, font=("나눔고딕", 12),
                                      validate="key", validatecommand=vcmd)
        self.password_entry.pack(pady=(0,10))
        self.password_entry.bind('<KeyRelease>', lambda e: self._remove_korean(self.password_entry))

        tk.Label(frame, text="이름:", bg=WINDOW_BG, fg="white", font=("나눔고딕", 12, "bold")).pack(anchor=tk.W, pady=(0,2))
        self.name_entry = tk.Entry(frame, width=30, font=("나눔고딕", 12))
        self.name_entry.pack(pady=(0,10))

        tk.Label(frame, text="닉네임:", bg=WINDOW_BG, fg="white", font=("나눔고딕", 12, "bold")).pack(anchor=tk.W, pady=(0,2))
        self.nickname_entry = tk.Entry(frame, width=30, font=("나눔고딕", 12))
        self.nickname_entry.pack(pady=(0,10))

        btn_frame = tk.Frame(frame, bg=WINDOW_BG)
        btn_frame.pack(pady=10)
        signup_btn = tk.Button(btn_frame, text="회원가입", command=self.on_signup,
                              font=("나눔고딕", 12, "bold"), width=16)
        signup_btn.pack(side=tk.LEFT, padx=5)
        cancel_btn = tk.Button(btn_frame, text="취소", command=self.on_cancel,
                              font=("나눔고딕", 12, "bold"), width=16)
        cancel_btn.pack(side=tk.LEFT, padx=5)

        self.status_label = tk.Label(frame, text="", fg="red", bg=WINDOW_BG, font=("나눔고딕", 11))
        self.status_label.pack(pady=(10,0))

    def on_signup(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        name = self.name_entry.get().strip()
        nickname = self.nickname_entry.get().strip()
        if not email or not password or not name or not nickname:
            self.status_label.config(text="이메일, 비밀번호, 이름, 닉네임을 모두 입력하세요.")
            return
        try:
            req_data = {"email": email, "password": password, "username": name, "nickname": nickname, "role": "USER"}
            debug_print_main(f"[회원가입 요청] URL: {SIGNUP_URL} DATA: {req_data}")
            resp = requests.post(SIGNUP_URL, json=req_data)
            debug_print_main(f"[회원가입 응답] CODE: {resp.status_code} BODY: {resp.text}")
            if resp.status_code == 200:
                messagebox.showinfo("회원가입 성공", "회원가입이 성공적으로 완료되었습니다! 로그인 해주세요.")
                self.result = True
                self.destroy()
            else:
                messagebox.showerror("회원가입 실패", f"회원가입 실패: {resp.text}")
                self.status_label.config(text=f"회원가입 실패: {resp.text}", fg="red")
        except Exception as e:
            debug_print_main(f"[회원가입 예외] {e}")
            messagebox.showerror("오류", f"오류: {e}")
            self.status_label.config(text=f"오류: {e}", fg="red")

    def on_cancel(self):
        self.result = None
        self.destroy()

    def _remove_korean(self, entry):
        value = entry.get()
        import re
        new_value = re.sub(r"[\uac00-\ud7a3]", "", value)
        if value != new_value:
            entry.delete(0, tk.END)
            entry.insert(0, new_value)

class LoginDialog(tk.Toplevel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.title("로그인")
        self.geometry("400x260")
        self.resizable(False, False)
        self.configure(bg=WINDOW_BG)
        self.token = None
        self.refresh_token = None
        self.setup_ui()
        self.grab_set()
        self.focus_set()
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.result = None
        self.wait_window(self)

    def setup_ui(self):
        frame = tk.Frame(self, bg=WINDOW_BG)
        frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        # 한글 입력 방지 함수
        def no_korean_input(P):
            import re
            return not bool(re.search(r"[\uac00-\ud7a3]", P))
        vcmd = (self.register(no_korean_input), '%P')

        title = tk.Label(frame, text="DUET 대시보드 로그인", font=("나눔고딕", 16, "bold"), bg=WINDOW_BG, fg="white")
        title.pack(pady=(0, 20))

        tk.Label(frame, text="이메일:", bg=WINDOW_BG, fg="white", font=("나눔고딕", 12, "bold")).pack(anchor=tk.W, pady=(0,2))
        self.email_entry = tk.Entry(frame, width=30, font=("나눔고딕", 12), validate="key", validatecommand=vcmd)
        self.email_entry.pack(pady=(0,10))
        self.email_entry.bind('<KeyRelease>', lambda e: self._remove_korean(self.email_entry))

        tk.Label(frame, text="비밀번호:", bg=WINDOW_BG, fg="white", font=("나눔고딕", 12, "bold")).pack(anchor=tk.W, pady=(0,2))
        self.password_entry = tk.Entry(frame, show="*", width=30, font=("나눔고딕", 12), validate="key", validatecommand=vcmd)
        self.password_entry.pack(pady=(0,10))
        self.password_entry.bind('<KeyRelease>', lambda e: self._remove_korean(self.password_entry))

        btn_frame = tk.Frame(frame, bg=WINDOW_BG)
        btn_frame.pack(pady=10)
        login_btn = tk.Button(btn_frame, text="로그인", command=self.on_login,
                              font=("나눔고딕", 12, "bold"), width=16)
        login_btn.pack(side=tk.LEFT, padx=5)
        signup_btn = tk.Button(btn_frame, text="회원가입", command=self.open_signup,
                               font=("나눔고딕", 12, "bold"), width=16)
        signup_btn.pack(side=tk.LEFT, padx=5)
        cancel_btn = tk.Button(btn_frame, text="취소", command=self.on_cancel,
                               font=("나눔고딕", 12, "bold"), width=16)
        cancel_btn.pack(side=tk.LEFT, padx=5)

        self.status_label = tk.Label(frame, text="", fg="red", bg=WINDOW_BG, font=("나눔고딕", 11))
        self.status_label.pack(pady=(10,0))

    def on_login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        if not email or not password:
            self.status_label.config(text="이메일과 비밀번호를 입력하세요.")
            return
        try:
            req_data = {"email": email, "password": password}
            debug_print_main(f"[로그인 요청] URL: {LOGIN_URL} DATA: {req_data}")
            resp = requests.post(LOGIN_URL, json=req_data)
            debug_print_main(f"[로그인 응답] CODE: {resp.status_code} BODY: {resp.text}")
            if resp.status_code == 200:
                # 응답 헤더에서 토큰 추출
                self.token = (
                    resp.headers.get("accessToken") 
                    or resp.headers.get("Authorization") 
                    or resp.headers.get("access")
                )
                self.refresh_token = resp.headers.get("refreshToken")
                debug_print_main(f"[로그인 성공] accessToken(헤더): {str(self.token)[:10]}..., refreshToken(헤더): {str(self.refresh_token)[:10]}...")
                self.result = "login"
                self.destroy()
            else:
                # 서버에서 에러 메시지 추출 시도
                try:
                    err_json = resp.json()
                    err_msg = err_json.get("message") or resp.text
                except Exception:
                    err_msg = resp.text
                import tkinter.messagebox as messagebox
                messagebox.showerror("로그인 실패", f"로그인 실패: {err_msg}")
                self.status_label.config(text=f"로그인 실패: {err_msg}", fg="red")
        except Exception as e:
            debug_print_main(f"[로그인 예외] {e}")
            import tkinter.messagebox as messagebox
            messagebox.showerror("오류", f"오류: {e}")
            self.status_label.config(text=f"오류: {e}", fg="red")

    def open_signup(self):
        SignupDialog(self)

    def on_cancel(self):
        self.token = None
        self.refresh_token = None
        self.result = None
        self.destroy()

    def get_token(self):
        return self.token 

    def get_refresh_token(self):
        return self.refresh_token

    def _remove_korean(self, entry):
        value = entry.get()
        import re
        new_value = re.sub(r"[\uac00-\ud7a3]", "", value)
        if value != new_value:
            entry.delete(0, tk.END)
            entry.insert(0, new_value) 