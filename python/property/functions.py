import time
from datetime import datetime
from functools import wraps, lru_cache

def func_timer(func):
    @wraps(func)
    def wrap_func(*args, **kargs):
        print(f"Starting {func.__name__}...")
        print(f"The docstring says: {func.__doc__}")
        start = datetime.now()
        res = func(*args, **kargs)
        time_elapsed = (datetime.now() - start).total_seconds()
        print(f"The {func.__name__} took {time_elapsed} seconds")
        return res
    return wrap_func

@func_timer
def foo():
    time.sleep(5)

@lru_cache(maxsize=None)
def fib(n):
    """ Fibonacci with memoization"""
    if n < 2:
        return n
    return fib(n-1) + fib(n-2)

def fib_no_memo(n):
    """ Fibonacci without memoization"""
    if n < 2:
        return n
    return fib_no_memo(n-1) + fib_no_memo(n-2)

if __name__ == "__main__":
    # foo()
    # sleep = func_timer(time.sleep)
    # print(f"Testing now built-in {sleep.__name__}")
    # sleep(10)
    # print(f"Done {sleep.__name__}")

    print("Starting Fibonacci with memo")
    start = datetime.now()
    print(fib(40))
    time_elapsed = (datetime.now() - start).total_seconds()
    print(f"The Fibonacci with memo took {time_elapsed} seconds")
    print("Starting Fibonacci without memo")
    start = datetime.now()
    print(fib_no_memo(40))
    time_elapsed = (datetime.now() - start).total_seconds()
    print(f"The Fibonacci without memo took {time_elapsed} seconds")



