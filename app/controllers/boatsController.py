from fastapi import APIRouter, Depends
import os
import redis.asyncio as aioredis

router = APIRouter(prefix="/boats", tags=["Boats"])
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
BOAT_REGISTRY_KEY = "boat:registry"

async def get_redis():
    return await aioredis.from_url(REDIS_URL, decode_responses=True)

@router.get("/active")
async def list_active_boats(redis=Depends(get_redis)):
    boat_ids = await redis.smembers(BOAT_REGISTRY_KEY)
    out = []
    for bid in boat_ids:
        count = await redis.scard(f"boat:{bid}:clients")
        captain = await redis.get(f"boat:{bid}:captain") or ""
        mission = await redis.get(f"boat:{bid}:mission") or ""
        name = await redis.get(f"boat:{bid}:name") or ""
        out.append({
            "id": bid,
            "name": name,
            "connections": int(count),
            "captain": captain,
            "mission": mission
        })
    return out

@router.get("/{boat_id}/telemetry")
async def get_boat_telemetry(boat_id: str, redis=Depends(get_redis)):
    key = f"boat:{boat_id}:telemetry"
    data = await redis.hgetall(key)
    if not data:
        return {"error": "No telemetry found for this boat"}
    return data

@router.get("/{boat_id}/clients")
async def get_boat_clients(boat_id: str, redis=Depends(get_redis)):
    clients = await redis.smembers(f"boat:{boat_id}:clients")
    captain = await redis.get(f"boat:{boat_id}:captain") or ""
    return {"captain": captain, "clients": list(clients)}
