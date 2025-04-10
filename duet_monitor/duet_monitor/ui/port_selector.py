"""
포트 선택기 모듈
"""
import tkinter as tk
from tkinter import ttk
import serial.tools.list_ports
from typing import List, Optional
from ..core.serial_handler import SerialHandler
from ..config.settings import DEFAULT_PORT, DEFAULT_BAUD_RATE
import platform
import os

class PortSelector(ttk.LabelFrame):
    def __init__(self, parent: tk.Widget, serial_handler: SerialHandler):
        """포트 선택기 초기화"""
        super().__init__(parent, text="연결 설정")
        self.parent = parent
        self.serial_handler = serial_handler
        
        # UI 초기화
        self.setup_ui()
        
    def setup_ui(self):
        """UI 초기화"""
        # 메인 프레임
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 포트 선택
        port_frame = ttk.Frame(main_frame)
        port_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(port_frame, text="포트:").grid(row=0, column=0, sticky=tk.W, padx=5)
        
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(
            port_frame, 
            textvariable=self.port_var,
            values=self.get_available_ports(),
            state="readonly",
            width=15
        )
        self.port_combo.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # 첫 번째 포트 선택
        if self.port_combo['values']:
            self.port_combo.set(self.port_combo['values'][0])
            
        # 포트 새로고침 버튼
        self.refresh_button = ttk.Button(
            port_frame,
            text="새로고침",
            command=self.refresh_ports,
            width=8
        )
        self.refresh_button.grid(row=0, column=2, padx=5, sticky=tk.E)
        
        # 통신 속도 선택
        baud_frame = ttk.Frame(main_frame)
        baud_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(baud_frame, text="통신 속도:").grid(row=0, column=0, sticky=tk.W, padx=5)
        
        self.baud_var = tk.IntVar(value=DEFAULT_BAUD_RATE)
        self.baud_combo = ttk.Combobox(
            baud_frame,
            textvariable=self.baud_var,
            values=[9600, 19200, 38400, 57600, 115200],
            state="readonly",
            width=15
        )
        self.baud_combo.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # 기본 통신 속도 선택
        self.baud_combo.set(DEFAULT_BAUD_RATE)
        
        # 연결 버튼
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        self.connect_button = ttk.Button(
            button_frame,
            text="연결",
            command=self.connect,
            width=12
        )
        self.connect_button.pack(side=tk.LEFT, padx=5)
        
        self.disconnect_button = ttk.Button(
            button_frame,
            text="연결 해제",
            command=self.disconnect,
            width=12,
            state=tk.DISABLED
        )
        self.disconnect_button.pack(side=tk.LEFT, padx=5)
        
        # 상태 표시
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(status_frame, text="상태:").grid(row=0, column=0, sticky=tk.W, padx=5)
        
        self.status_label = ttk.Label(status_frame, text="연결 안됨")
        self.status_label.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # 포트 목록 초기화
        self.refresh_ports()
        
    def get_available_ports(self) -> List[str]:
        """사용 가능한 시리얼 포트 목록 반환"""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        if not ports:
            # 시스템 기본 포트 확인
            system_ports = []
            
            # 맥 OS의 일반적인 포트
            if platform.system() == "Darwin":
                for i in range(10):
                    for prefix in ["/dev/cu.usbmodem", "/dev/cu.usbserial"]:
                        test_port = f"{prefix}{i+1}101"
                        try:
                            # 포트가 존재하는지만 확인
                            if os.path.exists(test_port):
                                system_ports.append(test_port)
                        except:
                            pass
            
            # 윈도우의 일반적인 포트
            elif platform.system() == "Windows":
                for i in range(10):
                    system_ports.append(f"COM{i+1}")
            
            # 리눅스의 일반적인 포트
            else:
                for i in range(10):
                    test_port = f"/dev/ttyACM{i}"
                    try:
                        if os.path.exists(test_port):
                            system_ports.append(test_port)
                    except:
                        pass
                    
                    test_port = f"/dev/ttyUSB{i}"
                    try:
                        if os.path.exists(test_port):
                            system_ports.append(test_port)
                    except:
                        pass
            
            # 시스템 포트 중 존재하는 포트 찾기
            for port in system_ports:
                try:
                    if os.path.exists(port):
                        ports.append(port)
                except:
                    pass
                
            # 그래도 없으면 기본 포트 사용
            if not ports:
                print(f"사용 가능한 시리얼 포트를 찾을 수 없어 기본 포트({DEFAULT_PORT}) 사용")
                ports = [DEFAULT_PORT]
                
        return ports
        
    def refresh_ports(self):
        """포트 목록 새로고침"""
        self.port_combo['values'] = self.get_available_ports()
        if self.port_combo['values']:
            self.port_var.set(self.port_combo['values'][0])
            
    def connect(self):
        """시리얼 포트 연결"""
        port = self.port_var.get()
        baud_rate = self.baud_var.get()
        
        if not port:
            return
            
        # 시리얼 핸들러로 연결
        if self.serial_handler:
            if self.serial_handler.connect(port, baud_rate):
                # 연결 성공
                self.status_label.config(text=f"연결됨: {port}")
                self.connect_button.config(state=tk.DISABLED)
                self.disconnect_button.config(state=tk.NORMAL)
                self.port_combo.config(state=tk.DISABLED)
                self.baud_combo.config(state=tk.DISABLED)
            else:
                # 연결 실패
                self.status_label.config(text="연결 실패")
                
    def disconnect(self):
        """시리얼 포트 연결 해제"""
        if self.serial_handler:
            if self.serial_handler.close():
                # 연결 해제 성공
                self.status_label.config(text="연결 안됨")
                self.connect_button.config(state=tk.NORMAL)
                self.disconnect_button.config(state=tk.DISABLED)
                self.port_combo.config(state="readonly")
                self.baud_combo.config(state="readonly")
            else:
                # 연결 해제 실패
                self.status_label.config(text="연결 해제 실패")
                
    def get_port(self) -> Optional[str]:
        """현재 선택된 포트 반환"""
        return self.port_var.get()
        
    def get_baud_rate(self) -> int:
        """현재 선택된 통신 속도 반환"""
        return self.baud_var.get() 