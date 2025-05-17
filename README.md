# 🎛️ DUET 모니터링 시스템

> **실시간 센서 데이터 수집 · 시각화 · 저장 · 분석 · MQTT 연동까지 올인원 데스크탑 애플리케이션**

---

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📝 프로젝트 소개

**DUET 모니터링 시스템**은 시리얼 통신 기반의 다양한 센서 데이터를 실시간으로 수집하고, 직관적인 UI로 시각화하며, CSV로 저장/불러오기, 통계 분석, MQTT 서버 연동까지 지원하는 통합 데스크탑 애플리케이션입니다.

- **센서 데이터 실시간 수집 및 시각화**
- **CSV 저장/불러오기 및 통계 분석**
- **MQTT 서버 연동(REST API)**
- **다양한 모드(전체/경량/테스트) 및 직관적 UI**

---

## 🚀 주요 기능

- **실시간 센서 데이터 수집** : 시리얼 포트(USB 등)로 연결된 센서 데이터 실시간 수집
- **데이터 시각화** : 센서별 실시간 그래프, LED 디스플레이, 통계 요약, 데이터 테이블 제공
- **데이터 저장/불러오기** : CSV 파일로 데이터 저장 및 불러오기 지원
- **모드 전환** : 전체 모드/경량 모드/테스트 모드 지원 (명령행 인수 또는 UI에서 선택)
- **다중 센서 지원** : 여러 센서 데이터 동시 시각화 및 선택적 표시
- **직관적 UI** : 포트 선택, 센서 제어, 데이터 제어, 그래프/테이블/통계 등 다양한 UI 컴포넌트 제공
- **MQTT 연동** : 수집된 데이터를 외부 MQTT 서버(REST API)로 전송
- **로그인/회원가입** : 사용자 인증 및 토큰 기반 데이터 전송
- **Docker 환경 지원** : 라즈베리파이 에뮬레이션 및 개발 환경 제공

---

## 🖥️ UI 미리보기

- **제어 패널**: 포트 선택, 센서 선택, 데이터 수집/정지, CSV 저장/불러오기 등
- **실시간 그래프**: 센서별/다중 센서 실시간 그래프 시각화
- **LED 디스플레이**: 주요 센서값을 7-세그먼트 스타일로 표시
- **데이터 테이블**: 실시간 데이터 테이블 및 컬럼 자동 확장
- **통계 요약**: 센서별 실시간 통계(평균, 최대, 최소 등) 표시

---

## 📂 폴더 구조

```text
duet_monitor/
  ├── core/         # 데이터 처리, 시리얼 통신, CSV 핸들러 등 핵심 로직
  ├── ui/           # 메인 윈도우, 그래프, 테이블, LED, 제어 패널 등 UI
  ├── config/       # 설정 파일 및 센서/포트/단위 정보
  ├── utils/        # 보조 함수 및 유틸리티
  ├── mqtt/         # MQTT 연동 모듈
  ├── __main__.py   # 패키지 실행 진입점
  ├── main.py       # 메인 실행 파일
logs/               # 디버그 로그 저장
index.html          # 웹 기반 유즈케이스 다이어그램 예시
requirements.txt    # 의존성 목록
Dockerfile          # 도커 환경 설정
start.sh            # 실행 스크립트
```

---

## ⚡ 설치 방법

1. **Python 3.8 이상**이 필요합니다.
2. 의존성 설치:
   ```bash
   pip install -r requirements.txt
   ```
   또는 패키지 설치:
   ```bash
   pip install .
   ```

---

## ▶️ 실행 방법

### 1. 기본 실행

```bash
python -m duet_monitor.main
```

### 2. 명령행 옵션

| 옵션            | 설명                     |
| --------------- | ------------------------ |
| `--test`        | 테스트 모드(가상 데이터) |
| `--lightweight` | 경량 모드(간소화된 UI)   |
| `--full`        | 전체 모드(모든 기능)     |
| `--skipui`      | 모드 선택 UI 건너뛰기    |
| `--debug`       | 디버그 모드              |

예시:

```bash
python -m duet_monitor.main --full --debug
```

### 3. 패키지 설치 후 콘솔 명령어

```bash
duet-monitor
```

---

## 🛠️ 주요 의존성

- pyserial==3.5
- pandas==2.2.1
- matplotlib==3.8.3
- requests==2.32.3
- paho-mqtt==1.6.1

---

## 🔄 데이터 흐름 및 구조

```mermaid
graph TD;
    A[센서] --시리얼 통신--> B[SerialHandler]
    B --> C[DataProcessor]
    C --> D[CSV 저장/불러오기]
    C --> E[UI 시각화]
    C --> F[MQTT 전송]
    D -.CSV 파일.- G[사용자]
    E -.그래프/테이블/LED/통계.- G
    F -.REST API.- H[MQTT 서버]
```

---

## 🌐 MQTT/REST 연동

- 수집된 센서 데이터는 MQTT REST API(`https://smartair.site/mqtt/receive`)로 전송됩니다.
- 토큰 기반 인증 및 토픽별 데이터 전송 지원
- 네트워크 장애/오류 시 UI에 상태 표시 및 로그 기록

---

## 🐳 Docker 환경 지원

- 라즈베리파이 에뮬레이션 및 개발 환경 제공
- `Dockerfile` 참고 (qemu, usbutils 등 포함)
- 실제 센서 연결 없이 개발/테스트 가능

---

## 🗂️ 유즈케이스 다이어그램 (index.html)

- `index.html`에서 웹 기반 유즈케이스 다이어그램 확인 가능
- 주요 유즈케이스: 실시간 모니터링, 데이터 수집/시각화, AI 예측/감지, HVAC 제어, 에너지 관리 등

---

## 💡 참고 및 기타

- `logs/` 폴더에 디버그 로그가 저장됩니다.
- `start.sh`로 빠른 실행 가능
- `requirements.txt`에서 의존성 버전 확인

---

> 본 프로젝트는 오픈소스이며, 자유롭게 수정 및 배포하실 수 있습니다.
