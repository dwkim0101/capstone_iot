"""
설정 모듈
"""
import os
import platform
import matplotlib.font_manager as fm
from typing import Dict, List, Tuple, Any

# 애플리케이션 설정
APP_TITLE = "DUET 모니터링 시스템"
WINDOW_TITLE = "DUET 모니터링 시스템"
WINDOW_SIZE = "1200x800"
UPDATE_INTERVAL = 100  # ms

# 시리얼 통신 설정
DEFAULT_PORT = "/dev/ttyACM0" if platform.system() != "Windows" else "COM3"
DEFAULT_BAUD_RATE = 9600
SERIAL_TIMEOUT = 1.0
TIMEOUT = 1.0  # 시리얼 통신 타임아웃 (초)

# 데이터 수집 설정
MAX_DATA_POINTS = 1000  # 그래프에 표시될 최대 데이터 포인트 수
CSV_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
DEFAULT_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
# 디렉터리가 없으면 생성
os.makedirs(DEFAULT_DATA_DIR, exist_ok=True)

# 테이블 설정
TABLE_MAX_ROWS = 100  # 테이블에 표시할 최대 행 수

# 센서 단위 설정
SENSOR_UNITS: Dict[str, str] = {
    "temperature": "°C",
    "humidity": "%",
    "pressure": "hPa",
    "eco2": "ppm",
    "tvoc": "ppb",
    "pm10": "μg/m³",
    "pm25": "μg/m³",
    "pm100": "μg/m³",
    "pt1": "개/0.1L",
    "pt2": "개/0.1L",
    "pt3": "개/0.1L",
    "pt4": "개/0.1L",
    "pt5": "개/0.1L",
    "pt6": "개/0.1L"
}

# 한글 폰트 설정
def get_korean_font() -> str:
    """한글 지원 폰트 이름 반환"""
    # 기본 폰트
    default_font = "Malgun Gothic" if platform.system() == "Windows" else "AppleGothic"
    
    # 폰트 검색
    font_list = [f for f in fm.findSystemFonts() if default_font.lower() in os.path.basename(f).lower()]
    
    if font_list:
        font_name = font_list[0]
        print(f"사용 중인 한글 폰트: {os.path.basename(font_name).split('.')[0]}")
        print(f"{os.path.basename(font_name).split('.')[0]} 폰트 경로: {font_name}")
        return os.path.basename(font_name).split('.')[0]
    
    # 대체 폰트 검색
    alternative_fonts = [
        "NanumGothic", "NanumBarunGothic", "NanumMyeongjo",  # Windows/Linux
        "AppleGothic", "AppleMyungjo", "AppleSDGothicNeo"    # macOS
    ]
    
    for font in alternative_fonts:
        font_list = [f for f in fm.findSystemFonts() if font.lower() in os.path.basename(f).lower()]
        if font_list:
            font_name = font_list[0]
            print(f"사용 중인 한글 폰트: {os.path.basename(font_name).split('.')[0]}")
            return os.path.basename(font_name).split('.')[0]
    
    # 대체 폰트도 없으면 기본값 반환
    print(f"한글 폰트를 찾을 수 없어 기본값 사용: {default_font}")
    return default_font

# 폰트 설정
FONT_FAMILY = get_korean_font()
STATS_FONT = (FONT_FAMILY, 10, "bold")
TITLE_FONT = (FONT_FAMILY, 12, "bold")

# 그래프 색상
GRAPH_COLORS = {
    "temperature": "#1f77b4",  # 파란색
    "humidity": "#ff7f0e",     # 주황색
    "pressure": "#2ca02c",     # 녹색
    "eco2": "#d62728",        # 빨간색
    "tvoc": "#9467bd",        # 보라색
    "pm10": "#8c564b",        # 갈색
    "pm25": "#e377c2",        # 분홍색
    "pm100": "#7f7f7f",       # 회색
    "pt1": "#bcbd22",         # 연두색
    "pt2": "#17becf",         # 청록색
    "pt3": "#1f77b4",         # 파란색
    "pt4": "#ff7f0e",         # 주황색
    "pt5": "#2ca02c",         # 녹색
    "pt6": "#d62728"          # 빨간색
}

# LED 설정
LED_SIZE = 15
LED_COLORS = {
    "on": "#00FF00",   # 녹색
    "off": "#FF0000",  # 빨간색
    "idle": "#AAAAAA"  # 회색
} 