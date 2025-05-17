"""
DUET 모니터링 시스템 메인 실행 파일
"""
import tkinter as tk
from .core.serial_handler import SerialHandler
from .core.csv_handler import CsvHandler
from .core.data_processor import DataProcessor
from .ui.main_window import MainWindow

def main():
    """메인 함수"""
    # 메인 윈도우 생성
    root = tk.Tk()
    
    # 핸들러 초기화
    serial_handler = SerialHandler()
    csv_handler = CsvHandler()
    data_processor = DataProcessor()
    
    # 메인 윈도우 초기화
    app = MainWindow(root, serial_handler, csv_handler, data_processor)
    
    # 애플리케이션 실행
    app.run()

if __name__ == "__main__":
    main() 