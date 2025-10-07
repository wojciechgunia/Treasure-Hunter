import asyncio
import json
import redis.asyncio as aioredis
import paho.mqtt.client as mqtt
from datetime import datetime

# 🔧 Konfiguracja
REDIS_HOST = "redis"
REDIS_PORT = 6379
MQTT_BROKER = "mqtt"
MQTT_PORT = 1883
TOPIC_PREFIX = "boat"

# Struktura przechowująca informacje o połączeniach
# statek -> {phones: set(), captain: str, mission: id, mode: str}
boats_state = {}

# Redis klient
redis_client = None


async def init_redis():
    global redis_client
    redis_client = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    try:
        await redis_client.ping()
        print("✅ Connected to Redis")
    except Exception as e:
        print("❌ Redis connection error:", e)


# MQTT callbacki
def on_connect(client, userdata, flags, rc, properties=None):
    print(f"✅ MQTT Connected with result code {rc}")
    client.subscribe(f"{TOPIC_PREFIX}/+/status")
    client.subscribe(f"{TOPIC_PREFIX}/+/connect")
    client.subscribe(f"{TOPIC_PREFIX}/+/disconnect")
    client.subscribe(f"{TOPIC_PREFIX}/+/command")
    client.subscribe(f"{TOPIC_PREFIX}/+/telemetry")
    client.subscribe(f"{TOPIC_PREFIX}/+/camera")
    client.subscribe(f"{TOPIC_PREFIX}/+/sonar")


def on_message(client, userdata, msg):
    asyncio.run(handle_mqtt_message(msg.topic, msg.payload))


async def handle_mqtt_message(topic, payload):
    try:
        parts = topic.split("/")
        if len(parts) < 3:
            return
        boat_id = parts[1]
        event_type = parts[2]

        data = json.loads(payload.decode())

        if event_type == "connect":
            await handle_connect(boat_id, data)
        elif event_type == "disconnect":
            await handle_disconnect(boat_id, data)
        elif event_type == "status":
            await handle_status(boat_id, data)
        elif event_type == "command":
            await handle_command(boat_id, data)
        elif event_type in ["telemetry", "camera", "sonar"]:
            await handle_data(boat_id, event_type, data)
    except Exception as e:
        print("⚠️ Error in handle_mqtt_message:", e)


async def handle_connect(boat_id, data):
    username = data.get("username")
    if not username:
        return

    boat_key = f"boat:{boat_id}"
    current = await redis_client.hgetall(boat_key)
    phones = set(json.loads(current.get("phones", "[]")))

    phones.add(username)
    captain = current.get("captain")
    if not captain:
        captain = username

    await redis_client.hset(boat_key, mapping={
        "phones": json.dumps(list(phones)),
        "captain": captain,
        "updatedAt": datetime.utcnow().isoformat()
    })
    print(f"📡 {username} connected to boat {boat_id}")


async def handle_disconnect(boat_id, data):
    username = data.get("username")
    if not username:
        return

    boat_key = f"boat:{boat_id}"
    current = await redis_client.hgetall(boat_key)
    phones = set(json.loads(current.get("phones", "[]")))

    if username in phones:
        phones.remove(username)

    captain = current.get("captain")
    if captain == username:
        # Wybierz nowego kapitana losowo
        captain = next(iter(phones), "")

    await redis_client.hset(boat_key, mapping={
        "phones": json.dumps(list(phones)),
        "captain": captain,
        "updatedAt": datetime.utcnow().isoformat()
    })
    print(f"❌ {username} disconnected from boat {boat_id}")


async def handle_status(boat_id, data):
    await redis_client.hset(f"boat:{boat_id}", mapping={
        "status": json.dumps(data),
        "updatedAt": datetime.utcnow().isoformat()
    })


async def handle_command(boat_id, data):
    print(f"🧭 Command received for boat {boat_id}: {data}")


async def handle_data(boat_id, data_type, data):
    # dane telemetryczne / kamera / sonar
    await redis_client.publish(f"{TOPIC_PREFIX}/{boat_id}/{data_type}/update", json.dumps(data))

async def wait_for_mqtt():
    import time
    for i in range(10):
        try:
            client = mqtt.Client(protocol=mqtt.MQTTv311)
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            client.disconnect()
            print("✅ MQTT is available")
            return
        except Exception as e:
            print(f"⏳ Waiting for MQTT... ({i+1}/10)")
            time.sleep(3)
    raise RuntimeError("❌ MQTT broker not reachable")


async def main():
    await init_redis()

    client = mqtt.Client(protocol=mqtt.MQTTv311)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    await wait_for_mqtt()
    client.loop_start()

    print("🚀 MQTT Presence Worker running...")
    while True:
        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
