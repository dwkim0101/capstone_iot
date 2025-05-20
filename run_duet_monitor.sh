#!/bin/bash

# 프로젝트 루트 디렉토리로 이동 (스크립트 위치 기준)
cd "$(dirname "$0")"

# venv 디렉토리명
VENV_DIR="venv"

# requirements.txt 경로
REQ_FILE="requirements.txt"

# logs 디렉토리 생성
mkdir -p logs

# venv가 없으면 생성
if [ ! -d "$VENV_DIR" ]; then
    echo "[INFO] 가상환경(venv) 생성 중..."
    python3 -m venv "$VENV_DIR"
    echo "[INFO] venv 생성 완료. 패키지 설치 중..."
    source "$VENV_DIR/bin/activate"
    if [ -f "$REQ_FILE" ]; then
        pip install --upgrade pip
        pip install -r "$REQ_FILE"
    fi
    deactivate
fi

# venv 활성화
source "$VENV_DIR/bin/activate"

# main.py 실행 (모든 인자 전달, 로그 저장)
echo "[INFO] main.py 실행..."
python3 duet_monitor/main.py "$@" 2>&1 | tee logs/last_run.log

# venv 비활성화
deactivate 