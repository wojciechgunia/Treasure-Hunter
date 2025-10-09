import time
import random
import json
import paho.mqtt.client as mqtt

MQTT_BROKER = "localhost"  # albo "mqtt" jeśli uruchamiasz z kontenera
MQTT_PORT = 1883
TOPIC_PREFIX = "boats"
BOAT_ID = "posejdon-1"


def main():
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    # symulacja: łódka online
    payload = {
        "status": "online",
        "name": "Posejdon",
        "mission": "Exploration A1"
    }
    topic = f"{TOPIC_PREFIX}/{BOAT_ID}/status"

    print(f"➡️ Publikuję do {topic}: {payload}")
    client.publish(topic, json.dumps(payload))

    try:
        lat = 54.0
        lon = 18.5
        speed = 3.4

        # Utrzymuj aktywność przez 30 sekund
        for i in range(30):
            lat += random.uniform(-0.0005, 0.0005)  # zmiana szerokości geograficznej
            lon += random.uniform(-0.0005, 0.0005)  # zmiana długości geograficznej
            speed += random.uniform(-0.2, 0.2)  # zmiana prędkości

            # ograniczenie prędkości do sensownego zakresu
            speed = max(0, speed)

            client.publish(f"boats/{BOAT_ID}/telemetry", json.dumps({
                "lat": round(lat, 6),
                "lon": round(lon, 6),
                "speed": round(speed, 2)
            }), qos=1, retain=False)
            time.sleep(1)
    finally:
        payload["status"] = "idle"
        print(f"➡️ Publikuję do {topic}: {payload}")
        client.publish(topic, json.dumps(payload))

        client.disconnect()
        print("✅ Zakończono symulację.")

if __name__ == "__main__":
    main()