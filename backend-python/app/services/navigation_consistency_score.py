import math
import redis
import json
import os

redis_url = os.getenv()
redis_client = redis.Redis.from_url(redis_url)