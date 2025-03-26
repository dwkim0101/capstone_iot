"""
유틸리티 함수 모음
"""
import json
import datetime
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any, Optional, Set

def fix_json_string(json_str: str) -> Tuple[str, bool, str, str]:
    """
    불완전하거나 손상된 JSON 문자열을 복구하는 함수
    
    Args:
        json_str: 복구할 JSON 문자열
        
    Returns:
        Tuple[str, bool, str, str]: (수정된 JSON, 성공 여부, 수정 방법, 원본 오류)
    """
    try:
        # 먼저 원본 파싱 시도
        json.loads(json_str)
        return json_str, False, "", ""
    except json.JSONDecodeError as e:
        original_error = str(e)
        is_fixed = False
        method = ""
        
        # 전략 1: 따옴표 없는 키 수정
        if "Expecting property name" in original_error:
            parts = json_str.split(":")
            if len(parts) > 1:
                key = parts[0].strip()
                if not key.startswith('"') and not key.endswith('"'):
                    key = f'"{key}"'
                    json_str = f"{key}:{':'.join(parts[1:])}"
                    method += "_fixed_key"
                    is_fixed = True
                    
        # 전략 2: 따옴표 문제 수정
        quote_count = json_str.count('"')
        if quote_count % 2 != 0:
            json_str = json_str + '"'
            method += "_fixed_quotes"
            is_fixed = True
            
        # 전략 3: 쉼표 문제 수정
        if ",," in json_str:
            json_str = json_str.replace(",,", ",")
            method += "_fixed_commas"
            is_fixed = True
            
        if json_str.endswith(",}"):
            json_str = json_str[:-2] + "}"
            method += "_fixed_trailing_comma"
            is_fixed = True
            
        return json_str, is_fixed, method, original_error

def process_data_item(data: Dict[str, Any], existing_columns: Set[str]) -> Tuple[Optional[Dict[str, Any]], Set[str]]:
    """
    단일 데이터 아이템 처리
    
    Args:
        data: 처리할 데이터
        existing_columns: 기존 컬럼 목록
        
    Returns:
        Tuple[Optional[Dict[str, Any]], Set[str]]: (처리된 데이터, 새로운 컬럼 목록)
    """
    try:
        # 타임스탬프 추가
        if "timestamp" not in data:
            data["timestamp"] = datetime.datetime.now().isoformat()
            
        # 새로운 컬럼 확인
        new_columns = set(data.keys()) - existing_columns
        
        return data, new_columns
        
    except Exception as e:
        print(f"데이터 처리 오류: {e}")
        return None, set()

def get_unit_for_sensor(sensor_name: str) -> str:
    """
    센서 이름에 따른 단위 반환
    
    Args:
        sensor_name: 센서 이름
        
    Returns:
        str: 센서의 단위
    """
    sensor_name = sensor_name.lower()
    if "temperature" in sensor_name:
        return "°C"
    elif "humidity" in sensor_name:
        return "%"
    elif "pressure" in sensor_name:
        return "hPa"
    elif "pm" in sensor_name or "particle" in sensor_name:
        return "μg/m³"
    elif "voltage" in sensor_name:
        return "V"
    elif "current" in sensor_name:
        return "A"
    return "" 