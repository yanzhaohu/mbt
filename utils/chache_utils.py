from cachetools import LRUCache

cache = LRUCache(maxsize=50)

def cache_put(k,value):
    cache[k] =value

def cache_get(k):
    return cache.get(k)