"""
DUET 모니터링 애플리케이션 메인 모듈
"""
import sys
import tkinter as tk
import argparse
import traceback
import os
import time
import threading
import requests

from duet_monitor.ui.main_window import MainWindow
from duet_monitor.ui.mode_selector import ModeSelector, debug_print
from duet_monitor.core.serial_handler import SerialHandler
from duet_monitor.core.csv_handler import CsvHandler
from duet_monitor.core.data_processor import DataProcessor
from duet_monitor.ui.login_dialog import LoginDialog
from duet_monitor.mqtt.mqtt_client import mqtt_publish_only, last_mqtt_response, last_mqtt_status_code
from duet_monitor.mqtt.mqtt_config import BROKER, TOPIC
from duet_monitor.utils.debug import debug_print_main
from duet_monitor.config.api_config import LOGIN_URL, SIGNUP_URL, REISSUE_URL

# 디버깅 상수
DEBUG = True

def debug_print_main(*args, **kwargs):
    """메인 모듈 디버깅 메시지 출력"""
    if DEBUG:
        message = " ".join(str(arg) for arg in args)
        print("[메인 모듈 디버그]", message, **kwargs)
        
        # 디버그 로그 파일이 있으면 파일에도 기록
        if hasattr(debug_print_main, 'log_file') and debug_print_main.log_file:
            try:
                debug_print_main.log_file.write(f"[메인 모듈 디버그] {message}\n")
                debug_print_main.log_file.flush()  # 즉시 기록
            except:
                pass
        
        sys.stdout.flush()  # 즉시 출력 반영

def create_debug_file():
    """디버그 로그 파일 생성"""
    if DEBUG:
        try:
            debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
            os.makedirs(debug_dir, exist_ok=True)
            
            debug_file_path = os.path.join(debug_dir, f"debug_{time.strftime('%Y%m%d_%H%M%S')}.log")
            debug_print_main.log_file = open(debug_file_path, 'w', encoding='utf-8')
            
            debug_print_main(f"디버그 로그 파일 생성됨: {debug_file_path}")
            debug_print_main(f"Python 버전: {sys.version}")
            debug_print_main(f"시스템 정보: {sys.platform}")
            
            return debug_print_main.log_file
        except Exception as e:
            print(f"디버그 로그 파일 생성 오류: {e}")
    return None

def close_debug_file():
    """디버그 로그 파일 닫기"""
    if DEBUG and hasattr(debug_print_main, 'log_file') and debug_print_main.log_file:
        try:
            debug_print_main.log_file.close()
            print(f"디버그 로그 파일 닫힘")
        except:
            pass

def parse_args():
    """명령행 인수 파싱"""
    parser = argparse.ArgumentParser(description='DUET 모니터링 시스템')
    parser.add_argument('--test', action='store_true', help='테스트 모드로 실행')
    parser.add_argument('--lightweight', action='store_true', help='경량 모드로 실행')
    parser.add_argument('--full', action='store_true', help='전체 모드로 실행')
    parser.add_argument('--skipui', action='store_true', help='모드 선택 UI 건너뛰기')
    parser.add_argument('--debug', action='store_true', help='디버그 모드로 실행')
    parser.add_argument('--test401', action='store_true', help='401 테스트 옵션')
    args = parser.parse_args()
    
    # 디버그 옵션이 지정된 경우 글로벌 상수 설정
    global DEBUG
    DEBUG = args.debug or DEBUG
    
    # --full과 --lightweight가 동시에 지정된 경우 경고
    if args.full and args.lightweight:
        print("경고: --full과 --lightweight가 동시에 지정되었습니다. --full이 우선합니다.")
        args.lightweight = False
    
    # --full 또는 --lightweight가 지정된 경우 UI 건너뛰기
    if args.full or args.lightweight:
        args.skipui = True
    
    return args

def show_mode_selector(root):
    """모드 선택 대화상자 표시"""
    debug_print_main("모드 선택 대화상자 표시 시작")
    
    try:
        # 루트 윈도우 표시 후 포커스
        root.deiconify()
        root.update()
        
        # 잠시 대기
        root.after(100)
        
        # 모드 선택 대화상자 생성
        mode_selector = ModeSelector(root)
        
        # 대화상자에서 선택된 모드 가져오기
        selected_mode = mode_selector.get_selected_mode()
        debug_print_main(f"선택된 모드: {selected_mode}")
        
        return selected_mode
    except Exception as e:
        debug_print_main(f"모드 선택 대화상자 표시 오류: {e}")
        debug_print_main(traceback.format_exc())
        return "full"  # 오류 발생 시 기본값 반환

def main():
    """메인 함수"""
    # 디버그 로그 파일 생성
    debug_file = create_debug_file()
    token = None
    refresh_token = None
    try:
        debug_print_main("애플리케이션 시작")
        # 명령행 인수 파싱
        args = parse_args()
        debug_print_main(f"명령행 인수: {args}")
        # 401 테스트 옵션 추가
        test_401 = hasattr(args, 'test401') and args.test401
        if not hasattr(args, 'test401'):
            test_401 = '--test401' in sys.argv
        # 루트 윈도우 생성
        root = tk.Tk()
        root.withdraw()  # 초기에는 숨김
        debug_print_main("루트 윈도우 생성 및 숨김")
        # 1. 로그인/회원가입 대화상자
        login_dialog = LoginDialog(root)
        token = login_dialog.get_token()
        # refresh_token도 받아오기 (LoginDialog에서 확장 필요)
        if hasattr(login_dialog, 'get_refresh_token'):
            refresh_token = login_dialog.get_refresh_token()
            debug_print_main(f"[로그인] refresh_token: {str(refresh_token)[:10]}..." if refresh_token else "[로그인] refresh_token: None")
        else:
            refresh_token = None
            debug_print_main("[로그인] LoginDialog에서 refresh_token을 반환하지 않음.")
        if not token:
            debug_print_main("로그인/회원가입 취소 또는 실패. 프로그램 종료.")
            print("로그인 또는 회원가입이 필요합니다. 프로그램을 종료합니다.")
            return
        debug_print_main(f"로그인/회원가입 성공, accessToken: {str(token)[:10]}...")
        # 시리얼 데이터 → MQTT 콜백 함수 정의
        mqtt_first_result = {'shown': False}
        status_message_type = {"current": None}
        status_message_after_id = {"id": None}
        def reissue_token(refresh_token):
            try:
                if not refresh_token or not isinstance(refresh_token, str) or not refresh_token.strip():
                    debug_print_main("[토큰 재발급 요청] refresh_token이 None/빈값/비문자열입니다. 재로그인 유도.")
                    return None, None
                debug_print_main(f"[토큰 재발급 요청] refresh_token: {str(refresh_token)[:10]}...")
                headers = {"Content-Type": "application/json"}
                # 배열로 보내는 테스트
                resp = requests.post(REISSUE_URL, json={"refreshToken": [refresh_token]}, headers=headers, timeout=5)
                debug_print_main(f"[토큰 재발급 응답] status: {resp.status_code}, body: {resp.text}")
                if resp.status_code == 200:
                    data = resp.json()
                    debug_print_main(f"[토큰 재발급 성공] accessToken: {str(data.get('accessToken'))[:10]}..., refreshToken: {str(data.get('refreshToken'))[:10]}...")
                    return data.get("accessToken"), data.get("refreshToken")
                else:
                    debug_print_main(f"[토큰 재발급 실패] {resp.status_code} {resp.text}")
                    return None, None
            except Exception as e:
                debug_print_main(f"[토큰 재발급 예외] {e}")
                return None, None
        def on_serial_data(data):
            try:
                debug_print_main(f"[main.py:on_serial_data] 콜백 진입: {data}")
                debug_print_main(f"[on_serial_data] last_mqtt_status_code: {last_mqtt_status_code}, last_mqtt_response: {last_mqtt_response}")
            except Exception as e:
                print(f"[main.py:on_serial_data] 콜백 진입 debug_print_main 예외: {e}")
            nonlocal token, refresh_token, test_401
            if not token:
                debug_print_main("[MQTT 전송 오류] 토큰이 없습니다. 데이터 전송 불가.")
                print("[MQTT 전송 오류] 토큰이 없습니다. 데이터 전송 불가.")
                return
            try:
                import copy
                data_copy = copy.deepcopy(data)
                if 'timestamp' in data_copy and hasattr(data_copy['timestamp'], 'isoformat'):
                    data_copy['timestamp'] = data_copy['timestamp'].isoformat()
            except Exception as e:
                debug_print_main(f"[on_serial_data] data 복사/타입 변환 예외: {e}")
                print(f"[on_serial_data] data 복사/타입 변환 예외: {e}")
                return
            try:
                debug_print_main(f"[on_serial_data] mqtt_publish_only 호출 직전: {data_copy}")
                topic_dynamic = f"smartair/{data_copy.get('id', 1)}/airquality"
                if test_401:
                    globals()['last_mqtt_status_code'] = 401
                    globals()['last_mqtt_response'] = '테스트용 401 강제 발생'
                    code = globals()['last_mqtt_status_code']
                    msg = globals()['last_mqtt_response']
                else:
                    mqtt_publish_only(topic_dynamic, data_copy, token)
                    from duet_monitor.mqtt.mqtt_client import last_mqtt_status_code, last_mqtt_response
                    code = last_mqtt_status_code
                    msg = last_mqtt_response
                debug_print_main(f"[on_serial_data] MQTT 응답 코드: {code}, 메시지: {msg}")
                print(f"[DEBUG][after mqtt_publish_only] last_mqtt_status_code: {code}, last_mqtt_response: {msg}")
                # 401 에러 발생 시 토큰 재발급 시도
                if code == 401:
                    import tkinter.messagebox as messagebox
                    debug_print_main(f"[on_serial_data] 401 발생, refresh_token: {str(refresh_token)[:10]}...")
                    # refresh_token이 있으면 재발급 시도 (test_401도 동일하게 동작)
                    if refresh_token:
                        new_token, new_refresh_token = reissue_token(refresh_token)
                        if new_token and new_refresh_token:
                            token = new_token
                            refresh_token = new_refresh_token
                            debug_print_main("토큰 재발급 성공, 토큰 갱신 완료. MQTT 재전송 시도.")
                            # test_401 모드 해제: 이후부터는 실제 서버와 통신
                            test_401 = False
                            # 재시도 1회
                            if test_401:
                                globals()['last_mqtt_status_code'] = 401
                                globals()['last_mqtt_response'] = '테스트용 401 강제 발생'
                                code = globals()['last_mqtt_status_code']
                                msg = globals()['last_mqtt_response']
                            else:
                                mqtt_publish_only(topic_dynamic, data_copy, token)
                                from duet_monitor.mqtt.mqtt_client import last_mqtt_status_code, last_mqtt_response
                                code = last_mqtt_status_code
                                msg = last_mqtt_response
                            debug_print_main(f"[on_serial_data] 재시도 후 MQTT 응답 코드: {code}, 메시지: {msg}")
                            if code == 401:
                                debug_print_main("[on_serial_data] 토큰 재발급 후에도 401. 프로그램 종료.")
                                messagebox.showerror("인증 오류", "토큰 재발급 후에도 인증에 실패했습니다. 프로그램을 종료합니다.")
                                root.quit()
                                return
                        else:
                            debug_print_main("토큰 재발급 실패. 로그인 다이얼로그로 전환.")
                            messagebox.showwarning("인증 만료", "토큰 재발급에 실패했습니다. 다시 로그인 해주세요.")
                            login_dialog = LoginDialog(root)
                            token = login_dialog.get_token()
                            if hasattr(login_dialog, 'get_refresh_token'):
                                refresh_token = login_dialog.get_refresh_token()
                                debug_print_main(f"[재로그인] refresh_token: {str(refresh_token)[:10]}..." if refresh_token else "[재로그인] refresh_token: None")
                            else:
                                refresh_token = None
                                debug_print_main("[재로그인] LoginDialog에서 refresh_token을 반환하지 않음.")
                            if not token:
                                debug_print_main("[재로그인] 재로그인 실패. 프로그램 종료.")
                                messagebox.showerror("인증 오류", "재로그인에 실패했습니다. 프로그램을 종료합니다.")
                                root.quit()
                                return
                    else:
                        debug_print_main("refresh_token 없음. 로그인 다이얼로그로 전환.")
                        messagebox.showwarning("인증 만료", "토큰이 만료되었습니다. 다시 로그인 해주세요.")
                        login_dialog = LoginDialog(root)
                        token = login_dialog.get_token()
                        if hasattr(login_dialog, 'get_refresh_token'):
                            refresh_token = login_dialog.get_refresh_token()
                            debug_print_main(f"[재로그인] refresh_token: {str(refresh_token)[:10]}..." if refresh_token else "[재로그인] refresh_token: None")
                        else:
                            refresh_token = None
                            debug_print_main("[재로그인] LoginDialog에서 refresh_token을 반환하지 않음.")
                        if not token:
                            debug_print_main("[재로그인] 재로그인 실패. 프로그램 종료.")
                            messagebox.showerror("인증 오류", "재로그인에 실패했습니다. 프로그램을 종료합니다.")
                            root.quit()
                            return
                # 501 또는 581 에러 발생 시 센서 등록 시도
                if code == 581:
                    serial_number = data_copy.get('id') or data_copy.get('serialNumber')
                    if serial_number:
                        success = register_sensor(serial_number, "DUET 센서", token)
                        if success:
                            debug_print_main(f"[센서 등록 성공] serialNumber: {serial_number}, MQTT 재전송 시도")
                        else:
                            debug_print_main(f"[센서 등록 실패 또는 이미 등록됨] serialNumber: {serial_number}, 그래도 MQTT 재전송 시도")
                        import time
                        time.sleep(1)  # 서버 반영 대기
                        for i in range(3):
                            mqtt_publish_only(topic_dynamic, data_copy, token)
                            from duet_monitor.mqtt.mqtt_client import last_mqtt_status_code, last_mqtt_response
                            code = last_mqtt_status_code
                            msg = last_mqtt_response
                            debug_print_main(f"[센서 등록 후 MQTT 재전송 {i+1}회] 응답 코드: {code}, 메시지: {msg}")
                            if code != 581:
                                break
                            time.sleep(1)
                    else:
                        debug_print_main("[센서 등록 실패] serialNumber 없음")
                error_msg = f"[MQTT-REST 오류] (코드: {code}) {msg}"
                app.root.after(0, show_status_message, error_msg, "red", 5000, "error")
            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                print(f"[on_serial_data 예외] {e}\n{tb}")
                debug_print_main(f"[on_serial_data 예외] {e}\n{tb}")
                if not mqtt_first_result['shown']:
                    import tkinter.messagebox as messagebox
                    messagebox.showerror("MQTT 오류", f"MQTT 전송 오류: {e}")
                    mqtt_first_result['shown'] = True
                print(f"[MQTT 전송 오류] {e}")
        # 핸들러 초기화 (콜백에 MQTT 연동)
        debug_print_main("핸들러 초기화 중...")
        data_processor = DataProcessor()
        serial_handler = SerialHandler()
        serial_handler.add_data_callback(on_serial_data)
        csv_handler = CsvHandler()
        debug_print_main("핸들러 초기화 완료")
        # 초기 경량 모드 설정
        is_lightweight = args.lightweight
        # --full 옵션이 지정된 경우 전체 모드로 강제 설정
        if args.full:
            is_lightweight = False
            debug_print_main("전체 모드 옵션이 지정됨")
        debug_print_main(f"초기 경량 모드 설정: {is_lightweight}")
        # UI 선택을 건너뛰지 않는 경우
        if not args.skipui:
            debug_print_main("모드 선택 UI 표시 필요")
            # 테스트를 위해 루트 윈도우를 잠시 표시
            root.deiconify()
            root.title("DUET 모니터링 시스템 - 초기화 중")
            root.update()
            # 루트 윈도우가 준비되었는지 확인
            debug_print_main(f"루트 윈도우 상태: 표시됨={root.winfo_viewable()}, "
                          f"너비={root.winfo_width()}, 높이={root.winfo_height()}")
            # 모드 선택 대화상자 표시
            selected_mode = show_mode_selector(root)
            # 모드 선택 취소 시 기본 모드(전체 모드)로 실행
            if selected_mode is None:
                debug_print_main("모드 선택 취소됨, 기본 모드(전체 모드)로 실행")
                print("모드 선택 취소됨, 기본 모드(전체 모드)로 실행합니다.")
                is_lightweight = False
            else:
                # 선택된 모드로 설정
                is_lightweight = (selected_mode == "lightweight")
                debug_print_main(f"선택된 모드에 따라 경량 모드 설정: {is_lightweight}")
        else:
            debug_print_main("모드 선택 UI 건너뛰기 요청됨")
        # 루트 윈도우 표시
        root.deiconify()
        debug_print_main("루트 윈도우 표시")
        # 메인 윈도우 초기화
        debug_print_main("메인 윈도우 초기화 시작")
        app = MainWindow(root, serial_handler, csv_handler, data_processor)
        app.status_message_type = status_message_type
        debug_print_main("메인 윈도우 초기화 완료")
        # UI 상태 메시지 안전 출력 함수
        def show_status_message(msg, color="red", duration=5000, msg_type=None):
            print(f"[DEBUG][show_status_message] 상태바 메시지: {msg}, 색상: {color}, 타입: {msg_type}")
            app.status_label.config(text=msg, foreground=color)
            app.status_label.update_idletasks()  # 강제 UI 갱신
            print(f"[DEBUG][show_status_message] 실제 표시값: {app.status_label.cget('text')}")
            status_message_type["current"] = msg_type
            # 이전 예약 취소
            if status_message_after_id["id"] is not None:
                app.root.after_cancel(status_message_after_id["id"])
            def reset_status():
                if status_message_type["current"] == msg_type:
                    print("[DEBUG][show_status_message] 상태바 메시지 초기화")
                    app.status_label.config(text="데이터 수집 중...", foreground="blue")
                    app.status_label.update_idletasks()
                    status_message_type["current"] = None
                    status_message_after_id["id"] = None
            status_message_after_id["id"] = app.root.after(duration, reset_status)
        # 테스트 모드 설정
        if args.test:
            debug_print_main("테스트 모드 활성화")
            print("테스트 모드로 실행 중...")
            # 테스트 데이터 생성은 MainWindow 클래스에서 처리
        # 경량 모드 설정
        if is_lightweight:
            debug_print_main("경량 모드 활성화")
            print("경량 모드로 실행 중...")
            app.set_lightweight_mode(True)
        else:
            debug_print_main("전체 모드 활성화")
            print("전체 모드로 실행 중...")
            app.set_lightweight_mode(False)
        # 애플리케이션 실행
        debug_print_main("메인 루프 시작")
        app.run()
        debug_print_main("애플리케이션 종료")
    except Exception as e:
        debug_print_main(f"메인 함수 오류: {e}")
        debug_print_main(traceback.format_exc())
        # 오류 발생 시 사용자에게 메시지 표시
        try:
            import tkinter.messagebox as msgbox
            msgbox.showerror("오류 발생", f"애플리케이션 실행 중 오류가 발생했습니다:\n{str(e)}\n\n"
                           f"자세한 내용은 logs 폴더의 디버그 로그를 확인하세요.")
        except:
            print(f"심각한 오류 발생: {e}")
    finally:
        # 디버그 로그 파일 닫기
        close_debug_file()

def register_sensor(serial_number, name, token):
    url = "https://smartair.site/sensor"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "serialNumber": serial_number,
        "name": name
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=5)
        debug_print_main(f"[센서 등록 요청] status: {resp.status_code}, body: {resp.text}")
        return resp.status_code == 200
    except Exception as e:
        debug_print_main(f"[센서 등록 예외] {e}")
        return False

# 모듈 직접 실행 시
if __name__ == "__main__":
    main() 