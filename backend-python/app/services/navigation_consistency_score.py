import math
import redis
import json
import os


#shannon entropy
def click_entropy(clicks) -> float:
    if not clicks or len(clicks) < 2:
        return 0.0
    coords = [f"{c['x']},{c['y']}" for c in clicks]
    freq = {}
    for coord in coords:
        freq[coord] = freq.get(coord, 0) + 1
    entropy = 0.0
    total = len(coords)
    for count in freq.values():
        p = count / total
        entropy += (-p) * math.log2(p)
    max_entropy = math.log2(total) if total > 1 else 1
    return round(entropy / max_entropy if max_entropy else 0.0, 3)

def store_click_position(user_id, x: int, y: int):
    key = f"user:{user_id}:click_positions"
    database.redis_client.rpush(key, json.dumps({"x": x, "y": y}))

def navigation_consistency_score(user_id, int) -> float:
    key = f"user:{user_id}:click_positions"
    clicks = [json.loads(c) for c in database.redis_client.redis_client.lrange(key, 0, -1)]
    entropy = click_entropy(clicks)