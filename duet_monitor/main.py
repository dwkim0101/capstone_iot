"""
Duet 모니터링 대시보드 메인 실행 파일
"""
from ui.main_window import MainWindow

def main():
    """메인 함수"""
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main() 