import json
import datetime
import pandas as pd
import serial
import serial.tools.list_ports
import time
import os

# CSV 파일 경로 설정
csv_file = "duet_data.csv"

# 사용 가능한 시리얼 포트 목록 출력
ports = list(serial.tools.list_ports.comports())
print("사용 가능한 시리얼 포트:")
for i, port in enumerate(ports):
    print(f"{i+1}. {port.device} - {port.description}")

# 사용자에게 포트 선택 요청
port_index = 0
if len(ports) > 1:
    try:
        port_index = int(input("사용할 포트 번호를 선택하세요: ")) - 1
        if port_index < 0 or port_index >= len(ports):
            port_index = 0
            print("잘못된 입력입니다. 첫 번째 포트를 사용합니다.")
    except ValueError:
        print("잘못된 입력입니다. 첫 번째 포트를 사용합니다.")

# 선택된 포트가 없으면 종료
if not ports:
    print("사용 가능한 시리얼 포트가 없습니다.")
    exit(1)

# 시리얼 포트 설정
port = ports[port_index].device
baud_rate = 9600  # TelosAir Duet의 기본 보드레이트
print(f"포트 {port}에 연결 중...")

# 데이터 수집 개수 설정
num_samples = int(input("수집할 데이터 개수를 입력하세요(최소 10개 이상 권장): ") or "30")
num_samples = max(10, num_samples)  # 최소 10개 이상 확보

try:
    # 시리얼 포트 열기
    ser = serial.Serial(port, baud_rate, timeout=10)
    print(f"---- 포트 {port} 열림 ----")
    print(f"{num_samples}개의 데이터를 수집합니다. 잠시 기다려주세요...")
    
    # 시리얼 버퍼 초기화
    ser.reset_input_buffer()
    time.sleep(1)
    
    # 데이터 수집
    json_lines = []
    count = 0
    
    while count < num_samples:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            if line.startswith("{") and line.endswith("}"):
                try:
                    json_data = json.loads(line)
                    json_lines.append(json_data)
                    count += 1
                    print(f"데이터 {count}/{num_samples} 수집 중...", end="\r")
                except json.JSONDecodeError:
                    print(f"JSON 파싱 오류: {line}")
            time.sleep(0.1)
    
    print("\n데이터 수집 완료!")
    ser.close()
    
except serial.SerialException as e:
    print(f"시리얼 포트 오류: {e}")
    exit(1)

# 데이터가 있는지 확인
if not json_lines:
    print("JSON 데이터를 찾을 수 없습니다.")
    exit(1)

# 첫 번째 JSON 객체의 키 확인
print("첫 번째 JSON 객체 키:", json_lines[0].keys())

# CSV 데이터 준비
rows = []
for data in json_lines:
    # 기본 데이터 추가
    row = {}
    
    # JSON 데이터의 첫 번째 레벨 키를 모두 추가
    for key, value in data.items():
        if key != "pt1" and key != "pt2":
            row[key] = value
    
    # pt1 데이터 추가
    for key, value in data["pt1"].items():
        row[f"pt1_{key}"] = value
        
    # pt2 데이터 추가
    for key, value in data["pt2"].items():
        row[f"pt2_{key}"] = value
        
    rows.append(row)

# DataFrame으로 변환하여 처리
df = pd.DataFrame(rows)

# DataFrame 열 확인
print("DataFrame 열:", df.columns.tolist())

# 타임스탬프 생성
current_time = datetime.datetime.now()
if "sample_time" in df.columns:
    max_sample_time = int(df["sample_time"].max())  # int로 변환
    start_time = current_time - datetime.timedelta(milliseconds=max_sample_time)
    
    # sample_time을 이용해 실제 타임스탬프 생성하고 새로운 timestamp 열 추가
    df["timestamp"] = df["sample_time"].apply(
        lambda x: (start_time + datetime.timedelta(milliseconds=int(x))).strftime("%Y-%m-%d %H:%M:%S")
    )
else:
    # sample_time이 없으면 현재 시간에서 약간의 시간차를 두고 생성
    df["timestamp"] = [
        (current_time - datetime.timedelta(seconds=len(df)-i)).strftime("%Y-%m-%d %H:%M:%S")
        for i in range(len(df))
    ]

# 타임스탬프를 맨 앞으로 정렬
cols = df.columns.tolist()
cols.remove("timestamp")
cols = ["timestamp"] + cols

df = df[cols]

# CSV 파일로 저장
df.to_csv(csv_file, index=False)
print(f"CSV 파일이 생성되었습니다: {csv_file}")
print(f"총 {len(df)}개의 데이터가 저장되었습니다.")

# 확인용으로 처음 몇 줄 출력
print("\n처음 5줄 데이터:")
print(df.head())