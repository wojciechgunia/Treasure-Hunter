# mqttWorker.py
import asyncio
import json
import redis.asyncio as aioredis
import paho.mqtt.client as mqtt
import threading
from datetime import datetime
import random
import os

# ----------------------
# Konfiguracja
# ----------------------
REDIS_HOST = "redis"
REDIS_PORT = 6379
MQTT_BROKER = "mqtt"
MQTT_PORT = 1883
TOPIC_PREFIX = "boats"

# ----------------------
# Globalne obiekty
# ----------------------
loop = asyncio.get_event_loop()
redis_client: aioredis.Redis = None
mqtt_client: mqtt.Client = None

# ----------------------
# Redis init
# ----------------------
async def init_redis():
    global redis_client
    redis_client = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    try:
        await redis_client.ping()
        print("✅ Connected to Redis")
    except Exception as e:
        print("❌ Redis connection error:", e)
        raise e

# ----------------------
# Handlery
# ----------------------

async def handle_status(boat_id: str, data):
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            data = {"status": data}

    status = data.get("status", "unknown")

    # Sprawdź bieżący status w Redis
    current_status = await redis_client.hget(f"boat:{boat_id}", "status")
    if current_status == status:
        return  # brak zmian, nie publikujemy i nie zapisujemy

    # Zapis do Redis
    await redis_client.hset(f"boat:{boat_id}", mapping={
        "status": status,
        "updatedAt": datetime.utcnow().isoformat()
    })

    # Retained topic dla klientów
    mqtt_client.publish(
        f"{TOPIC_PREFIX}/{boat_id}/status",
        json.dumps({"status": status}),
        qos=1,
        retain=True
    )

    # Aktualizacja rejestru aktywnych łodzi
    if status == "online":
        await redis_client.sadd("boat:registry", boat_id)
        await redis_client.set(f"boat:{boat_id}:name", data.get("name", f"Boat {boat_id}"))
        await redis_client.expire(f"boat:{boat_id}:name", 3600)
    elif status == "idle":
        await redis_client.srem("boat:registry", boat_id)
        await redis_client.delete(f"boat:{boat_id}:telemetry")
        await redis_client.delete(f"boat:{boat_id}:clients")
        await redis_client.delete(f"boat:{boat_id}:captain")
        await redis_client.delete(f"boat:{boat_id}:name")

    print(f"📌 Status updated for boat {boat_id}: {status}")

async def handle_telemetry(boat_id: str, data: dict):
    key = f"boat:{boat_id}:telemetry"
    data["updatedAt"] = datetime.utcnow().isoformat()
    await redis_client.hset(key, mapping=data)
    await redis_client.expire(key, 3600)
    print(f"📡 Telemetry saved for boat {boat_id}: {data}")

async def handle_presence(boat_id: str, data: dict):
    """
    data = {
        "client_id": "user-42-device-1",
        "username": "John",
        "status": "online"  # lub "offline" jeśli LWT
    }
    """
    client_id = data.get("client_id")
    username = data.get("username")
    status = data.get("status", "online")
    if not client_id or not username:
        return

    clients_key = f"boat:{boat_id}:clients"
    captain_key = f"boat:{boat_id}:captain"

    if status == "online":
        # Dodaj klienta
        await redis_client.sadd(clients_key, client_id)
        captain = await redis_client.get(captain_key)
        if not captain:
            # Pierwszy klient -> kapitan
            await redis_client.set(captain_key, client_id)
            mqtt_client.publish(f"{TOPIC_PREFIX}/{boat_id}/events",
                                json.dumps({"event": "captainChanged", "newCaptain": client_id}),
                                qos=1, retain=False)
    elif status == "offline":
        # Usuń klienta
        await redis_client.srem(clients_key, client_id)
        captain = await redis_client.get(captain_key)
        if captain == client_id:
            # Losowanie nowego kapitana
            remaining = await redis_client.smembers(clients_key)
            new_captain = random.choice(list(remaining)) if remaining else ""
            await redis_client.set(captain_key, new_captain)
            mqtt_client.publish(f"{TOPIC_PREFIX}/{boat_id}/events",
                                json.dumps({"event": "captainChanged", "newCaptain": new_captain}),
                                qos=1, retain=False)

    # Aktualizacja licznika klientów
    count = await redis_client.scard(clients_key)
    mqtt_client.publish(f"{TOPIC_PREFIX}/{boat_id}/clients/count",
                        json.dumps({"count": int(count)}),
                        qos=1, retain=True)

    print(f"👥 Presence updated for boat {boat_id}: {client_id} -> {status}")

# ----------------------
# Tryb łodzi
# ----------------------
async def handle_mode(boat_id: str, data: dict):
    mode = data.get("mode")
    if mode not in ["man", "auto", "way"]:
        return

    await redis_client.set(f"boat:{boat_id}:mode", mode)
    mqtt_client.publish(f"{TOPIC_PREFIX}/{boat_id}/mode",
                        json.dumps({"mode": mode}),
                        qos=1, retain=True)

    # Powiadom klientów
    mqtt_client.publish(f"{TOPIC_PREFIX}/{boat_id}/events",
                        json.dumps({"event": "modeChanged", "mode": mode}),
                        qos=1, retain=False)
    print(f"⚙️ Mode updated for {boat_id}: {mode}")

# ----------------------
# Command / Control
# ----------------------
async def handle_control(boat_id: str, data: dict):
    # man mode control
    left = max(-80, min(80, int(data.get("left", 0))))
    right = max(-80, min(80, int(data.get("right", 0))))

    await redis_client.hset(f"boat:{boat_id}:control", mapping={
        "left": left,
        "right": right,
        "updatedAt": datetime.utcnow().isoformat()
    })

    mqtt_client.publish(f"{TOPIC_PREFIX}/{boat_id}/control",
                        json.dumps({"left": left, "right": right}),
                        qos=1, retain=False)
    print(f"🚀 Control sent for {boat_id}: left={left}, right={right}")

async def handle_command(boat_id: str, data: dict):
    cmd = data.get("command")
    if not cmd:
        return

    mqtt_client.publish(f"{TOPIC_PREFIX}/{boat_id}/commands",
                        json.dumps(data),
                        qos=1, retain=False)

    # Opcjonalnie powiadom klientów
    if cmd in ["missionChange", "reqReset", "start", "stop", "nextWaypoint"]:
        mqtt_client.publish(f"{TOPIC_PREFIX}/{boat_id}/events",
                            json.dumps({"event": cmd, **data}),
                            qos=1, retain=False)

    print(f"🧭 Command sent for {boat_id}: {data}")

# ----------------------
# Router wiadomości MQTT
# ----------------------
async def route_mqtt_message(topic: str, payload: bytes):
    try:
        parts = topic.split("/")
        if len(parts) < 3:
            return

        boat_id = parts[1]
        event_type = parts[2]
        data = json.loads(payload.decode())

        if event_type == "status":
            await handle_status(boat_id, data)
        elif event_type == "telemetry":
            await handle_telemetry(boat_id, data)
        elif event_type == "presence":
            await handle_presence(boat_id, data)
        elif event_type == "mode":
            await handle_mode(boat_id, data)
        elif event_type == "control":
            await handle_control(boat_id, data)
        elif event_type == "command":
            await handle_command(boat_id, data)

    except Exception as e:
        print(f"⚠️ Error routing MQTT message: {e}")

# ----------------------
# MQTT
# ----------------------
def on_connect(client, userdata, flags, rc, properties=None):
    print(f"✅ MQTT Connected with result code {rc}")
    client.subscribe(f"{TOPIC_PREFIX}/+/status")
    client.subscribe(f"{TOPIC_PREFIX}/+/telemetry")
    client.subscribe(f"{TOPIC_PREFIX}/+/presence/+")
    # później dodamy kolejne topic

def on_message(client, userdata, msg):
    if msg.retain:
        return

    asyncio.run_coroutine_threadsafe(
        route_mqtt_message(msg.topic, msg.payload),
        loop
    )

def start_mqtt_loop():
    global mqtt_client
    mqtt_client = mqtt.Client(client_id="worker_1", protocol=mqtt.MQTTv311)  # <-- unikalny ID
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_forever()

async def init_mqtt():
    for i in range(10):
        try:
            test_client = mqtt.Client(protocol=mqtt.MQTTv311)
            test_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            test_client.disconnect()
            print("✅ MQTT broker is available")
            break
        except Exception:
            print(f"⏳ Waiting for MQTT... ({i+1}/10)")
            await asyncio.sleep(3)
    else:
        raise RuntimeError("❌ MQTT broker not reachable")

    threading.Thread(target=start_mqtt_loop, daemon=True).start()

# ----------------------
# Główna pętla
# ----------------------
async def main():
    await init_redis()
    await init_mqtt()
    print("🚀 MQTT Worker running...")
    while True:
        await asyncio.sleep(10)

if __name__ == "__main__":
    loop.run_until_complete(main())
