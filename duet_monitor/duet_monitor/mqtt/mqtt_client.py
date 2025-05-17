import json
from paho.mqtt import client as mqtt_client
from duet_monitor.utils.debug import debug_print_main

def publish_mqtt(token, topic, payload, broker):
    try:
        debug_print_main(f"[MQTT] publish_mqtt 함수 진입: broker={broker}, topic={topic}, client_id=smartair-pub-{token[:8]}")
        print(f"[MQTT] publish_mqtt 함수 진입: broker={broker}, topic={topic}")
        client_id = f"smartair-pub-{token[:8]}"
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                debug_print_main("✅ MQTT 연결 성공")
                print("✅ MQTT 연결 성공")
                # Swagger 명세에 따라 payload는 JSON string이어야 함
                mqtt_message = {
                    "topic": topic,
                    "payload": json.dumps(payload, default=str)
                }
                msg = json.dumps(mqtt_message, ensure_ascii=False)
                debug_print_main(f"[MQTT] 발행 데이터: {msg}")
                print(f"[MQTT] 발행 데이터: {msg}")
                client.publish(topic, msg, qos=1)
            else:
                debug_print_main(f"❌ MQTT 연결 실패: {rc}")
                print(f"❌ MQTT 연결 실패: {rc}")

        def on_publish(client, userdata, mid):
            debug_print_main("✅ 메시지 발행 성공")
            print("✅ 메시지 발행 성공")
            client.disconnect()

        def on_disconnect(client, userdata, rc):
            debug_print_main(f"🔌 MQTT 연결 종료: rc={rc}")
            print(f"🔌 MQTT 연결 종료: rc={rc}")

        client = mqtt_client.Client(client_id)
        debug_print_main("[MQTT] 콜백 등록")
        print("[MQTT] 콜백 등록")
        client.on_connect = on_connect
        client.on_publish = on_publish
        client.on_disconnect = on_disconnect
        debug_print_main("[MQTT] connect 호출 직전")
        print("[MQTT] connect 호출 직전")
        client.connect(broker)
        debug_print_main("[MQTT] loop_forever 호출")
        print("[MQTT] loop_forever 호출")
        client.loop_forever()
    except Exception as e:
        debug_print_main(f"[MQTT 예외] {e}")
        print(f"[MQTT 예외] {e}") 