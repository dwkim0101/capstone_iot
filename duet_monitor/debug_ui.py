import tkinter as tk
from duet_monitor.core.serial_handler import SerialHandler
from duet_monitor.core.csv_handler import CsvHandler
from duet_monitor.core.data_processor import DataProcessor
from duet_monitor.ui.main_window import MainWindow

def main():
    # 핸들러 초기화
    serial_handler = SerialHandler()
    csv_handler = CsvHandler()
    data_processor = DataProcessor()
    
    # 테스트 데이터 생성
    data_processor.generate_test_data(100)
    
    # 메인 윈도우 생성
    root = tk.Tk()
    app = MainWindow(root, serial_handler, csv_handler, data_processor)
    
    # 테스트 데이터로 LED 디스플레이 업데이트
    if hasattr(app, 'led_display'):
        latest_values = data_processor.get_latest_values()
        app.led_display.update_leds(latest_values)
    
    # 테스트 데이터로 통계 업데이트
    if hasattr(app, 'stats_view'):
        latest_values = data_processor.get_latest_values()
        app.stats_view.update_stats(latest_values)
    
    # 테스트 데이터로 테이블 업데이트
    if hasattr(app, 'data_table'):
        df = data_processor.get_dataframe()
        app.data_table.update_table(df)
    
    # 애플리케이션 실행
    app.run()

if __name__ == "__main__":
    main() 