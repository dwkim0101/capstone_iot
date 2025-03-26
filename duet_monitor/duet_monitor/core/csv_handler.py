"""
CSV 파일 핸들러 모듈
"""
import pandas as pd
import csv
import os
from typing import Dict, Any, Optional, List

class CsvHandler:
    def __init__(self):
        """CSV 핸들러 초기화"""
        self.file_path: Optional[str] = None
        self.csv_file = None
        self.csv_writer = None
        self.header_written = False
        
    def initialize(self, file_path: str) -> bool:
        """
        CSV 파일 초기화
        
        Args:
            file_path: CSV 파일 경로
            
        Returns:
            bool: 성공 여부
        """
        try:
            # 이전 파일이 열려있으면 닫기
            self.close()
            
            # 디렉토리 확인
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 파일 열기
            self.file_path = file_path
            self.csv_file = open(file_path, 'w', newline='', encoding='utf-8')
            self.csv_writer = csv.writer(self.csv_file)
            self.header_written = False
            
            print(f"CSV 파일 초기화됨: {file_path}")
            return True
            
        except Exception as e:
            print(f"CSV 파일 초기화 실패: {e}")
            self.close()
            return False
            
    def close(self) -> bool:
        """
        CSV 파일 닫기
        
        Returns:
            bool: 성공 여부
        """
        if self.csv_file:
            try:
                self.csv_file.close()
                self.csv_file = None
                self.csv_writer = None
                self.header_written = False
                return True
                
            except Exception as e:
                print(f"CSV 파일 닫기 실패: {e}")
                return False
                
        return True
        
    def append_data(self, data: Dict[str, Any]) -> bool:
        """
        CSV 파일에 데이터 추가
        
        Args:
            data: 추가할 데이터
            
        Returns:
            bool: 성공 여부
        """
        if not self.csv_file or not self.csv_writer:
            print("CSV 파일이 초기화되지 않았습니다.")
            return False
            
        try:
            # 헤더 작성 (첫 번째 데이터인 경우)
            if not self.header_written:
                self.csv_writer.writerow(data.keys())
                self.header_written = True
                
            # 데이터 작성
            self.csv_writer.writerow(data.values())
            self.csv_file.flush()  # 즉시 디스크에 기록
            
            return True
            
        except Exception as e:
            print(f"CSV 데이터 추가 실패: {e}")
            return False
            
    def append_batch(self, data_list: List[Dict[str, Any]]) -> bool:
        """
        CSV 파일에 데이터 배치 추가
        
        Args:
            data_list: 추가할 데이터 리스트
            
        Returns:
            bool: 성공 여부
        """
        if not data_list:
            return True
            
        if not self.csv_file or not self.csv_writer:
            print("CSV 파일이 초기화되지 않았습니다.")
            return False
            
        try:
            # 헤더 작성 (첫 번째 데이터인 경우)
            if not self.header_written:
                self.csv_writer.writerow(data_list[0].keys())
                self.header_written = True
                
            # 데이터 작성
            for data in data_list:
                self.csv_writer.writerow(data.values())
                
            self.csv_file.flush()  # 즉시 디스크에 기록
            
            return True
            
        except Exception as e:
            print(f"CSV 데이터 배치 추가 실패: {e}")
            return False
            
    def save_dataframe(self, df: pd.DataFrame, file_path: str) -> bool:
        """
        데이터프레임을 CSV 파일로 저장
        
        Args:
            df: 저장할 데이터프레임
            file_path: 저장할 파일 경로
            
        Returns:
            bool: 성공 여부
        """
        try:
            # 디렉토리 확인
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # CSV로 저장
            df.to_csv(file_path, index=False, encoding='utf-8')
            
            print(f"데이터프레임 저장됨: {file_path}")
            return True
            
        except Exception as e:
            print(f"데이터프레임 저장 실패: {e}")
            return False
            
    def load_csv(self, file_path: str) -> Optional[pd.DataFrame]:
        """
        CSV 파일을 데이터프레임으로 로드
        
        Args:
            file_path: 로드할 파일 경로
            
        Returns:
            Optional[pd.DataFrame]: 로드된 데이터프레임 (실패 시 None)
        """
        try:
            # CSV 파일 읽기
            df = pd.read_csv(file_path, encoding='utf-8')
            
            # 타임스탬프 컬럼이 있으면 datetime으로 변환
            if 'timestamp' in df.columns:
                try:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                except:
                    pass
                    
            print(f"CSV 파일 로드됨: {file_path}")
            return df
            
        except Exception as e:
            print(f"CSV 파일 로드 실패: {e}")
            return None 