# SmartAir 대시보드 API 및 인증 관련 상수

API_BASE = "https://smartair.site"
AUTH_URL = f"{API_BASE}/auth"
LOGIN_URL = f"{API_BASE}/login"
SIGNUP_URL = f"{API_BASE}/join"
REISSUE_URL = f"{API_BASE}/reissue"
SNAPSHOT_URL = f"{API_BASE}/snapshots"  # 스냅샷 API 엔드포인트
MQTT_RECEIVE_URL = f"{API_BASE}/mqtt/receive"  # MQTT 데이터 수신 엔드포인트
# 필요시 추가 엔드포인트
# DASHBOARD_DATA_URL = f"{API_BASE}/your-endpoint"