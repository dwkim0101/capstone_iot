"""
데이터 처리 모듈
"""
import pandas as pd
from typing import Dict, Any, List, Set, Optional
from ..utils.helpers import process_data_item

class DataProcessor:
    def __init__(self, max_rows: int = 10000):
        """
        데이터 처리기 초기화
        
        Args:
            max_rows: 최대 행 수
        """
        self.df = pd.DataFrame()
        self.max_rows = max_rows
        self.existing_columns: Set[str] = set()
        
    def update_dataframe(self, data: Dict[str, Any]) -> bool:
        """
        단일 데이터로 DataFrame 업데이트
        
        Args:
            data: 업데이트할 데이터
            
        Returns:
            bool: 성공 여부
        """
        try:
            row, new_columns = process_data_item(data, self.existing_columns)
            if row is None:
                return False
                
            # 새로운 컬럼 추가
            if new_columns:
                for col in new_columns:
                    if col not in self.df.columns:
                        self.df[col] = None
                self.existing_columns.update(new_columns)
                
            # 행 추가
            self.df = pd.concat([self.df, pd.DataFrame([row])], ignore_index=True)
            
            # 최대 행 수 제한
            if len(self.df) > self.max_rows:
                self.df = self.df.tail(self.max_rows)
                
            return True
            
        except Exception as e:
            print(f"DataFrame 업데이트 오류: {e}")
            return False
            
    def update_dataframe_batch(self, data_list: List[Dict[str, Any]]) -> bool:
        """
        데이터 리스트로 DataFrame 일괄 업데이트
        
        Args:
            data_list: 업데이트할 데이터 리스트
            
        Returns:
            bool: 성공 여부
        """
        try:
            new_rows = []
            new_columns = set()
            
            # 데이터 처리
            for data in data_list:
                row, cols = process_data_item(data, self.existing_columns)
                if row is not None:
                    new_rows.append(row)
                    if cols:
                        new_columns.update(cols)
                        
            if not new_rows:
                return False
                
            # 새로운 컬럼 추가
            if new_columns:
                for col in new_columns:
                    if col not in self.df.columns:
                        self.df[col] = None
                self.existing_columns.update(new_columns)
                
            # 행 추가
            self.df = pd.concat([self.df, pd.DataFrame(new_rows)], ignore_index=True)
            
            # 최대 행 수 제한
            if len(self.df) > self.max_rows:
                self.df = self.df.tail(self.max_rows)
                
            return True
            
        except Exception as e:
            print(f"DataFrame 일괄 업데이트 오류: {e}")
            return False
            
    def get_dataframe(self) -> pd.DataFrame:
        """
        현재 DataFrame 반환
        
        Returns:
            pd.DataFrame: 현재 DataFrame
        """
        return self.df
        
    def get_column_names(self) -> List[str]:
        """
        컬럼 이름 리스트 반환
        
        Returns:
            List[str]: 컬럼 이름 리스트
        """
        return list(self.df.columns)
        
    def get_latest_values(self) -> Dict[str, Any]:
        """
        최신 데이터 값 반환
        
        Returns:
            Dict[str, Any]: 최신 데이터 값
        """
        if self.df.empty:
            return {}
        return self.df.iloc[-1].to_dict()
        
    def clear(self):
        """DataFrame 초기화"""
        self.df = pd.DataFrame()
        self.existing_columns.clear() 