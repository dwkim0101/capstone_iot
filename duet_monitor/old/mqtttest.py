import json
import random
from paho.mqtt import client as mqtt_client

broker = '52.78.203.239'  # EC2 퍼블릭 IP
port = 1883
topic = 'smartair/1/1/airquality'
client_id = f'external-pub-client-{random.randint(0, 10000)}'

payload = {
  "type": 2,
  "id": 817,
  "sample_time": 773988,
  "pt1": {
    "pm10_standard": 22,
    "pm25_standard": 37,
    "pm100_standard": 39,
    "particles_03um": 3867,
    "particles_05um": 1132,
    "particles_10um": 283,
    "particles_25um": 15,
    "particles_50um": 2,
    "particles_100um": 1
  },
  "pt2": {
    "pm10_standard": 18,
    "pm25_standard": 29,
    "pm100_standard": 36,
    "particles_03um": 3468,
    "particles_05um": 940,
    "particles_10um": 191,
    "particles_25um": 22,
    "particles_50um": 10,
    "particles_100um": 4
  },
  "temperature": 29.47,
  "hum": 38.22,
  "pressure": 399,
  "tvoc": 6,
  "eco2": 400,
  "rawh2": 12656,
  "rawethanol": 1647
}

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker!")
        msg = json.dumps(payload)
        # 발행 후 on_publish 콜백이 호출됨
        client.publish(topic, msg, qos=1)
    else:
        print(f"❌ Failed to connect, return code {rc}")

def on_publish(client, userdata, mid):
    print("✅ Message published successfully")
    client.disconnect()  # 발행이 끝난 후 안전하게 연결 종료

def on_disconnect(client, userdata, rc):
    print(f"🔌 Disconnected with return code {rc}")

def run():
    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1, client_id)
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect
    client.enable_logger()
    client.connect(broker, port)
    client.loop_forever()  # 콜백이 모두 끝날 때까지 블로킹

if __name__ == '__main__':
    run()

