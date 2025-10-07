from fastapi import APIRouter, Depends
import os
import redis.asyncio as aioredis

router = APIRouter(prefix="/boats", tags=["Boats"])
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
BOAT_REGISTRY_KEY = "boat:registry"

async def get_redis():
    return await aioredis.from_url(REDIS_URL, decode_responses=True)

@router.get("/active")
async def list_active_boats(redis = Depends(get_redis)):
    boat_ids = await redis.smembers(BOAT_REGISTRY_KEY)
    out = []
    for b in boat_ids:
        bid = b
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
