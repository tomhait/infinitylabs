import time
from datetime import datetime
from functools import wraps

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
    """ This is foo here"""
    time.sleep(5)

if __name__ == "__main__":
    foo()
    sleep = func_timer(time.sleep)
    print(f"Testing now built-in {sleep.__name__}")
    sleep(10)
    print(f"Done {sleep.__name__}")

