import redis
from django.conf import settings

redis_client = redis.StrictRedis(host=getattr(settings, 'REDIS_HOST', 'localhost'), port=getattr(settings, 'REDIS_PORT', 6379), db=0)

POPULAR_SEARCHES_KEY = 'popular_searches'

def cache_popular_searches(searches):
    redis_client.set(POPULAR_SEARCHES_KEY, str(searches))

def get_popular_searches():
    searches = redis_client.get(POPULAR_SEARCHES_KEY)
    if searches:
        return eval(searches)
    return []
