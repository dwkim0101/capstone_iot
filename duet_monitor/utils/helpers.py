"""
유틸리티 함수 모음
"""
import json
import datetime
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any, Optional

def fix_json_string(json_str: str) -> Tuple[str, bool, str, str]:
    """
    불완전하거나 손상된 JSON 문자열을 복구하는 함수
    
    Args:
        json_str: 복구할 JSON 문자열
        
    Returns:
        Tuple[str, bool, str, str]: (수정된 JSON, 성공 여부, 수정 방법, 원본 오류)
    """
    original_str = json_str
    is_fixed = False
    method = "none"
    original_error = ""
    
    # 이미 유효한 JSON인지 확인
    try:
        json.loads(json_str)
        return json_str, False, "already_valid", ""
    except json.JSONDecodeError as e:
        original_error = str(e)
        
    try:
        # 전략 1: 불균형 중괄호 수정
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        
        if open_braces > close_braces:
            json_str = json_str + '}' * (open_braces - close_braces)
            method = "added_closing_braces"
            is_fixed = True
        elif close_braces > open_braces:
            json_str = '{' * (close_braces - open_braces) + json_str
            method = "added_opening_braces"
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
            
        # 수정된 JSON 유효성 검사
        if is_fixed:
            try:
                json.loads(json_str)
                return json_str, True, method, original_error
            except json.JSONDecodeError:
                pass
                
        # 전략 4: 키-값 쌍 구조 추정 복구
        if '"' in json_str:
            try:
                if not json_str.startswith('{'): 
                    json_str = '{' + json_str
                    method += "_added_opening_brace"
                if not json_str.endswith('}'): 
                    json_str = json_str + '}'
                    method += "_added_closing_brace"
                
                parts = json_str[1:-1].split(',')
                reconstructed_parts = []
                
                for part in parts:
                    if part.strip():
                        if ':' not in part:
                            continue
                        
                        key_value = part.split(':', 1)
                        key = key_value[0].strip()
                        value = key_value[1].strip() if len(key_value) > 1 else ""
                        
                        if not (key.startswith('"') and key.endswith('"')):
                            key = f'"{key.strip("\"")}"'
                            
                        if value and not value.startswith('"') and not value.endswith('"'):
                            try:
                                float(value)
                            except ValueError:
                                if not (value.startswith('{') or value.startswith('[')):
                                    value = f'"{value.strip("\"")}"'
                        
                        reconstructed_parts.append(f"{key}:{value}")
                
                reconstructed_json = '{' + ','.join(reconstructed_parts) + '}'
                json.loads(reconstructed_json)
                method += "_key_value_reconstruction"
                return reconstructed_json, True, method, original_error
                
            except Exception:
                pass
        
        return original_str, False, "no_valid_fix", original_error
        
    except Exception as error:
        return original_str, False, "error_during_fix", str(error)

def process_data_item(data: Dict[str, Any], existing_columns: set) -> Tuple[Optional[Dict[str, Any]], set]:
    """
    단일 데이터 항목을 처리하여 행 데이터 반환
    
    Args:
        data: 처리할 데이터 딕셔너리
        existing_columns: 기존 컬럼 집합
        
    Returns:
        Tuple[Optional[Dict[str, Any]], set]: (처리된 행 데이터, 새로운 컬럼 집합)
    """
    if not data or not isinstance(data, dict):
        return None, None
    
    try:
        row = {}
        new_columns = set()
        
        # 타임스탬프 처리
        if 'timestamp' in data:
            row['timestamp'] = data['timestamp']
        
        # 기본 필드 추출
        exclude_keys = {'_fixed', '_original_error', '_recovery_method'}
        
        # 모든 최상위 키-값 쌍 처리
        for key, value in data.items():
            if key in exclude_keys:
                continue
                
            if isinstance(value, dict):
                # 중첩된 객체 평탄화
                for sub_key, sub_value in value.items():
                    full_key = f"{key}_{sub_key}"
                    row[full_key] = sub_value
                    if full_key not in existing_columns:
                        new_columns.add(full_key)
            else:
                # 기본 키-값
                row[key] = value
                if key not in existing_columns:
                    new_columns.add(key)
        
        return row, new_columns
            
    except Exception as e:
        print(f"데이터 항목 처리 오류: {e}")
        return None, None

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