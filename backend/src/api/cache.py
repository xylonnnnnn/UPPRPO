import hashlib
import json
import logging

from fastapi import Request
from fastapi_cache.decorator import cache
from fastapi_cache import FastAPICache

from auth import decode_token_for_cache

logger = logging.getLogger(__name__)

def pins_key_builder(func, namespace, request: Request, response, *args, **kwargs):
    auth_header = request.headers.get("authorization", "")
    user_id = "anon"
    if auth_header.startswith("Bearer "):
        try:
            payload = decode_token_for_cache(auth_header[7:])
            user_id = payload.get("sub", "anon")
        except:
            pass

    key_data = {
        "path": request.url.path,
        "page": request.query_params.get("page", "1"),
        "size": request.query_params.get("size", "20"),
        "user_id": user_id
    }
    key_str = json.dumps(key_data, sort_keys=True)
    key_hash = hashlib.md5(key_str.encode()).hexdigest()
    return f"cache:{namespace}:pins:{key_hash}"


async def invalidate_pins_cache():
    try:
        backend = FastAPICache.get_backend()
        if not backend:
            logger.warning("FastAPICache not initialized, skipping invalidation")
            return

        redis = backend.redis
        async for key in redis.scan_iter("*pins*"):
            await redis.delete(key)
            logger.debug(f"Invalidated cache key: {key}")

    except Exception as e:
        logger.error(f"Failed to invalidate pins cache: {e}")