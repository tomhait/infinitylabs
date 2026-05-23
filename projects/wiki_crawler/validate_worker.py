import redis

r = redis.Redis(host='redis-server', port=6379, db=0, decode_responses=True)

BLOOM_FILTER_KEY = "visited_urls_bloom"


def initialize_bloom_filter():
    try:
        r.bf().reserve(BLOOM_FILTER_KEY, 0.01, 1000000)
        print(f"Bloom Filter '{BLOOM_FILTER_KEY}' initialized successfully.")
    except redis.exceptions.ResponseError as e:
        if "item exists" in str(e).lower():
            pass
        else:
            raise e

initialize_bloom_filter()

def add_visited_url(url):
    r.bf().add(BLOOM_FILTER_KEY, url)

def get_unvisited_urls(subpages):
    if not subpages: return None
    unvisited = set()
    for url in subpages:
        is_added = r.bf().add(BLOOM_FILTER_KEY, url)
        if is_added == 1:
            unvisited.add(url)
    if unvisited:
        return unvisited
    return None