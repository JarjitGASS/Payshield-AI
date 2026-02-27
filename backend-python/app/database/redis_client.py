import redis
import os
from dotenv import load_dotenv

redis_url = os.getenv("REDIS_URL") or "redis://localhost:6379/0"
redis_client = redis.Redis.from_url(redis_url)

