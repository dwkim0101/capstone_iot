"""
데이터 처리 모듈
"""
import pandas as pd
import numpy as np
import json
import ast
from typing import Dict, Any, List, Set, Optional, Tuple
from duet_monitor.utils.helpers import process_data_item
from datetime import datetime, timedelta
import random
from ..config.settings import SENSOR_UNITS

class DataProcessor:
    def __init__(self):
        """데이터 프로세서 초기화"""
        from duet_monitor.utils.debug import debug_print_main
        debug_print_main("[DataProcessor] __init__ 호출")
        self.data = []
        self.df = pd.DataFrame()
        self.max_rows = 1000
        self.selected_graph_sensor = None
        self.new_columns = set()  # 새로 추가된 컬럼 추적
        self.latest_values = {}
        debug_print_main(f"[DataProcessor] 초기 DataFrame 컬럼: {list(self.df.columns)}")

    def set_max_rows(self, max_rows: int) -> None:
        """
        메모리에 저장할 최대 데이터 행 수 설정
        
        Args:
            max_rows: 최대 행 수 (0은 제한 없음)
        """
        self.max_rows = max_rows
        
        # 현재 데이터가 제한을 초과하면 잘라내기
        if max_rows > 0 and len(self.df) > max_rows:
            self.df = self.df.tail(max_rows)
        
    def set_dataframe(self, df: pd.DataFrame) -> bool:
        """
        데이터프레임 직접 설정
        
        Args:
            df: 설정할 데이터프레임
            
        Returns:
            bool: 성공 여부
        """
        try:
            # 데이터프레임 설정
            self.df = df.copy()
            
            # 최신 값 업데이트
            if not df.empty:
                self.latest_values = df.iloc[-1].to_dict()
                
            # 새 컬럼 설정
            self.new_columns = set(df.columns)
            
            return True
        except Exception as e:
            print(f"데이터프레임 설정 오류: {e}")
            return False

    def update_dataframe(self, data: Dict[str, Any]) -> bool:
        """
        데이터프레임에 새 데이터 추가
        
        Args:
            data: 추가할 데이터 딕셔너리
            
        Returns:
            bool: 성공 여부
        """
        try:
            from duet_monitor.utils.debug import debug_print_main
            debug_print_main(f"[DataProcessor] update_dataframe 진입: {data}")
            try:
                processed_data = flatten_dict(data)
            except Exception as e:
                debug_print_main(f"[DataProcessor] flatten_dict 예외: {e} (data={data})")
                processed_data = {}
            debug_print_main(f"[DataProcessor] flatten_dict 결과: {processed_data}")
            new_df = pd.DataFrame([processed_data])
            debug_print_main(f"[DataProcessor] 새 데이터프레임 생성됨, 컬럼: {list(new_df.columns)}")
            new_columns = set(new_df.columns) - set(self.df.columns)
            if new_columns:
                debug_print_main(f"[DataProcessor] 새로운 컬럼 발견: {new_columns}")
            if self.df.empty:
                self.df = new_df
                debug_print_main("[DataProcessor] 최초 데이터프레임 생성")
            else:
                self.df = pd.concat([self.df, new_df], ignore_index=True)
                debug_print_main(f"[DataProcessor] 데이터프레임 연결됨, 현재 크기: {len(self.df)}")
            self.new_columns.update(new_columns)
            if len(self.df) > self.max_rows:
                self.df = self.df.tail(self.max_rows)
                debug_print_main(f"[DataProcessor] 최대 행 수 조정, 현재 크기: {len(self.df)}")
            self.latest_values = processed_data.copy()
            debug_print_main(f"[DataProcessor] 최신 값 업데이트됨: {self.latest_values}")
            debug_print_main(f"[DataProcessor] 최종 DataFrame 컬럼: {list(self.df.columns)}")
            debug_print_main(f"[DataProcessor] 최종 DataFrame 마지막 행: {self.df.iloc[-1].to_dict() if not self.df.empty else '없음'}")
            return True
        except Exception as e:
            import traceback
            debug_print_main(f"[DataProcessor] 데이터프레임 업데이트 오류: {e}\n{traceback.format_exc()}")
            print(f"데이터프레임 업데이트 오류: {e}")
            return False
    
    def update_dataframe_batch(self, data_list: List[Dict[str, Any]]) -> bool:
        """
        데이터프레임에 여러 데이터 일괄 추가
        
        Args:
            data_list: 추가할 데이터 딕셔너리 리스트
            
        Returns:
            bool: 성공 여부
        """
        try:
            from duet_monitor.utils.debug import debug_print_main
            debug_print_main(f"[DataProcessor] update_dataframe_batch 진입: {data_list}")
            if not data_list:
                debug_print_main("[DataProcessor] data_list 비어있음")
                return True
            processed_data_list = [flatten_dict(data) for data in data_list]
            debug_print_main(f"[DataProcessor] flatten_dict 결과(배치): {processed_data_list}")
            new_df = pd.DataFrame(processed_data_list)
            debug_print_main(f"[DataProcessor] 새 데이터프레임(배치) 생성됨, 컬럼: {list(new_df.columns)}")
            new_columns = set(new_df.columns) - set(self.df.columns)
            if self.df.empty:
                self.df = new_df
                debug_print_main("[DataProcessor] 최초 데이터프레임(배치) 생성")
            else:
                self.df = pd.concat([self.df, new_df], ignore_index=True)
                debug_print_main(f"[DataProcessor] 데이터프레임(배치) 연결됨, 현재 크기: {len(self.df)}")
            self.new_columns.update(new_columns)
            if len(self.df) > self.max_rows:
                self.df = self.df.tail(self.max_rows)
                debug_print_main(f"[DataProcessor] 최대 행 수 조정(배치), 현재 크기: {len(self.df)}")
            self.latest_values = processed_data_list[-1].copy()
            debug_print_main(f"[DataProcessor] 배치 최신 값 업데이트됨: {self.latest_values}")
            debug_print_main(f"[DataProcessor] 배치 최종 DataFrame 컬럼: {list(self.df.columns)}")
            debug_print_main(f"[DataProcessor] 배치 최종 DataFrame 마지막 행: {self.df.iloc[-1].to_dict() if not self.df.empty else '없음'}")
            return True
        except Exception as e:
            import traceback
            debug_print_main(f"[DataProcessor] 데이터프레임 배치 업데이트 오류: {e}\n{traceback.format_exc()}")
            print(f"데이터프레임 배치 업데이트 오류: {e}")
            return False
    
    def process_pt_data(self, data: Dict[str, Any]):
        """
        PT1, PT2 데이터를 개별 컬럼으로 처리
        
        Args:
            data: 처리할 데이터 딕셔너리
        """
        # PT1 처리
        if 'pt1' in data and data['pt1']:
            self.extract_pt_data(data, 'pt1')
            
        # PT2 처리
        if 'pt2' in data and data['pt2']:
            self.extract_pt_data(data, 'pt2')
    
    def extract_pt_data(self, data: Dict[str, Any], pt_key: str):
        """
        PT 데이터에서 각 값을 추출하여 새 컬럼으로 추가
        
        Args:
            data: 원본 데이터 딕셔너리
            pt_key: PT 키 (pt1 또는 pt2)
        """
        try:
            # PT 값 가져오기
            pt_value = data[pt_key]
            
            # 문자열이면 딕셔너리로 변환
            if isinstance(pt_value, str):
                try:
                    # JSON 형식으로 파싱 시도
                    pt_dict = json.loads(pt_value)
                except json.JSONDecodeError:
                    try:
                        # 딕셔너리 문자열로 파싱 시도
                        pt_dict = ast.literal_eval(pt_value)
                    except (ValueError, SyntaxError):
                        print(f"{pt_key} 데이터 파싱 실패: {pt_value}")
                        return
            elif isinstance(pt_value, dict):
                pt_dict = pt_value
            elif isinstance(pt_value, (int, float)):
                # 숫자 값이면 그대로 사용
                data[pt_key] = float(pt_value)
                return
            else:
                print(f"{pt_key} 데이터 타입 오류: {type(pt_value)}")
                return
                
            # 각 값을 개별 컬럼으로 추가
            for key, value in pt_dict.items():
                col_name = f"{pt_key}_{key}"
                data[col_name] = float(value)
                
            # 원본 PT 데이터 삭제
            del data[pt_key]
                
        except Exception as e:
            print(f"{pt_key} 데이터 처리 오류: {e}")
    
    def get_dataframe(self) -> pd.DataFrame:
        """
        데이터프레임 반환
        
        Returns:
            pd.DataFrame: 현재 데이터프레임
        """
        return self.df.copy()
    
    def get_columns(self) -> List[str]:
        """
        컬럼 이름 목록 반환
        
        Returns:
            List[str]: 컬럼 이름 리스트
        """
        return list(self.df.columns)
    
    def get_latest_values(self) -> Dict[str, Any]:
        """
        최신 값 반환
        
        Returns:
            Dict[str, Any]: 각 컬럼의 최신 값
        """
        return self.latest_values
    
    def get_new_columns(self) -> Set[str]:
        """
        새로 추가된 컬럼 목록 반환
        
        Returns:
            Set[str]: 새 컬럼 집합
        """
        return self.new_columns.copy()
    
    def reset_new_columns(self):
        """새로 추가된 컬럼 목록 초기화"""
        self.new_columns.clear()
    
    def clear_data(self):
        """데이터 초기화"""
        self.df = pd.DataFrame()
        self.new_columns.clear()
        self.latest_values = {}
    
    def generate_test_data(self, num_samples: int = 100) -> None:
        """
        테스트 데이터 생성 (개발용)
        
        Args:
            num_samples: 생성할 샘플 수
        """
        print(f"테스트 데이터 {num_samples}개 생성됨")
        
        # 현재 시간
        now = datetime.now()
        
        # 타임스탬프 생성 (최근 시간부터 과거 순으로)
        timestamps = [now - timedelta(seconds=i) for i in range(num_samples)]
        timestamps.reverse()  # 과거부터 현재 순으로 정렬
        
        # 기본 데이터
        data = []
        
        # 샘플 ID 설정
        sample_id = 817
        
        for i in range(num_samples):
            # 샘플 타임 값 생성 (밀리초 단위)
            sample_time = 795000 + (i * 10000)
            
            # PT1과 PT2 데이터 생성 (파티클 센서 데이터) - 문자열화하지 않고 딕셔너리 형태 유지
            pt1_data = {
                "pm10_standard": random.randint(1, 5),
                "pm25_standard": random.randint(3, 7),
                "pm100_standard": random.randint(3, 7),
                "particles_03um": random.randint(600, 900),
                "particles_05um": random.randint(150, 250),
                "particles_10um": random.randint(20, 50),
                "particles_25um": random.randint(0, 5),
                "particles_50um": random.randint(0, 2),
                "particles_100um": random.randint(0, 1)
            }
            
            pt2_data = {
                "pm10_standard": random.randint(1, 5),
                "pm25_standard": random.randint(3, 6),
                "pm100_standard": random.randint(3, 6),
                "particles_03um": random.randint(500, 800),
                "particles_05um": random.randint(150, 200),
                "particles_10um": random.randint(10, 40),
                "particles_25um": random.randint(0, 4),
                "particles_50um": random.randint(0, 1),
                "particles_100um": random.randint(0, 1)
            }
            
            # 샘플 데이터 생성 - pt1, pt2는 딕셔너리 형태 그대로 유지
            sample = {
                "type": 2,
                "id": sample_id,
                "sample_time": sample_time,
                "pt1": pt1_data,  # 직접 딕셔너리 할당
                "pt2": pt2_data,  # 직접 딕셔너리 할당
                "temperature": round(27.7 + random.uniform(-0.2, 0.2), 2),
                "hum": round(35.0 + random.uniform(-1.0, 1.5), 2),
                "pressure": 402,
                "tvoc": random.randint(0, 80),
                "eco2": 400 + (random.randint(0, 5) * 50 if random.random() > 0.8 else 0),
                "rawh2": random.randint(12400, 12900),
                "rawethanol": random.randint(940, 1200),
                "timestamp": timestamps[i]
            }
            
            data.append(sample)
            
        # 데이터프레임 생성
        df = pd.DataFrame(data)
        
        # 데이터프레임 저장 - 원본 데이터 그대로 저장
        self.df = df
        
        # 추가: 필드 타입 확인 및 경고 출력
        if not df.empty:
            for key in ['pt1', 'pt2']:
                if key in df.columns:
                    field_type = type(df[key].iloc[0])
                    print(f"필드 {key}의 타입: {field_type}")
        
        # 선택된 센서 필드 확인 및 출력
        selected_sensor = "pt1"  # 기본 센서로 pt1 선택
        unit = SENSOR_UNITS.get(selected_sensor, "")
        print(f"선택된 센서: {selected_sensor}, 단위: {unit}")
            
        # 최신 값 업데이트
        if not df.empty:
            self.latest_values = df.iloc[-1].to_dict()
            
        return df
        
    def filter_by_timerange(self, start_time: Optional[datetime] = None, 
                          end_time: Optional[datetime] = None) -> pd.DataFrame:
        """
        시간 범위로 데이터 필터링
        
        Args:
            start_time: 시작 시간
            end_time: 종료 시간
            
        Returns:
            pd.DataFrame: 필터링된 데이터프레임
        """
        if self.df.empty:
            return pd.DataFrame()
            
        filtered_df = self.df.copy()
        
        # 시작 시간 필터링
        if start_time:
            filtered_df = filtered_df[filtered_df['timestamp'] >= start_time]
            
        # 종료 시간 필터링
        if end_time:
            filtered_df = filtered_df[filtered_df['timestamp'] <= end_time]
            
        return filtered_df
        
    def get_statistics(self, column: str) -> Dict[str, float]:
        """
        특정 컬럼의 통계 정보 반환
        
        Args:
            column: 통계를 계산할 컬럼
            
        Returns:
            Dict[str, float]: 통계 정보
        """
        if self.df.empty or column not in self.df.columns:
            return {
                'mean': 0,
                'min': 0,
                'max': 0,
                'std': 0
            }
            
        stats = {
            'mean': self.df[column].mean(),
            'min': self.df[column].min(),
            'max': self.df[column].max(),
            'std': self.df[column].std()
        }
        
        return stats

    def set_selected_graph_sensor(self, sensor: str):
        """그래프에 표시할 센서 설정"""
        self.selected_graph_sensor = sensor
        
    def get_selected_graph_sensor(self) -> Optional[str]:
        """현재 선택된 그래프 센서 반환"""
        return self.selected_graph_sensor

# --- flatten_dict 유틸 함수 추가 ---
def flatten_dict(d, parent_key='', sep='_'):
    from duet_monitor.utils.debug import debug_print_main
    items = []
    for k, v in d.items():
        new_key = f'{parent_key}{sep}{k}' if parent_key else k
        try:
            if isinstance(v, dict):
                debug_print_main(f"[flatten_dict] dict 발견: {new_key}")
                items.extend(flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, (list, set, tuple)):
                debug_print_main(f"[flatten_dict] list/set/tuple 발견: {new_key}")
                items.append((new_key, str(v)))
            else:
                items.append((new_key, v))
        except Exception as e:
            debug_print_main(f"[flatten_dict] 예외: {e} (key={new_key}, value={v})")
            items.append((new_key, str(v)))
    debug_print_main(f"[flatten_dict] 결과: {items}")
    return dict(items)