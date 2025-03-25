"""
설정 파일 - 전역 상수 및 설정값 정의
"""

# 그래프 설정
MAX_DATA_POINTS = 500  # 그래프에 표시할 최대 데이터 포인트 수
UPDATE_INTERVAL = 100  # 대시보드 업데이트 간격 (밀리초)
DATA_BATCH_SIZE = 10  # 한번에 처리할 데이터 배치 크기

# 데이터 수집 설정
MAX_BUFFER_SIZE = 10000  # 버퍼 최대 크기 제한
MAX_DF_ROWS = 10000  # DataFrame 최대 행 수
MAX_DISPLAY_ROWS = 100  # 테이블에 표시할 최대 행 수

# 시리얼 포트 설정
DEFAULT_BAUD_RATES = ["9600", "19200", "38400", "57600", "115200"]
DEFAULT_BAUD_RATE = "9600"

# UI 설정
WINDOW_SIZE = "1280x800"
WINDOW_TITLE = "TelosAir Duet 실시간 모니터링 대시보드"

# LED 디스플레이 설정
LED_SIZES = [20, 30, 40, 50]
DEFAULT_LED_SIZE = 30
LED_COLORS = ["red", "green", "blue", "orange", "purple"]
DEFAULT_LED_COLOR = "red"
DEFAULT_LED_UPDATE_MS = 1000

# 한글 폰트 설정
FONT_FAMILY = 'AppleGothic'  # macOS
FONT_FAMILY_FALLBACK = 'NanumGothic'  # Windows/Linux 