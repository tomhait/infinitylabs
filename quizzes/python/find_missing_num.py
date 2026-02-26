import numpy as np
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
def find_missing_num(arr: np.ndarray):
    n = len(arr)
    tot_sum = n*(n+1)/2
    return tot_sum - sum(arr)

@func_timer
def find_missing_num_xor(arr: np.ndarray):
    n = len(arr)
    xor_sum = 0
    for i in range(n+1):
        xor_sum ^= i
    for num in arr:
        xor_sum ^= num
    return xor_sum

arr = np.arange(500)
print(find_missing_num_xor(arr))
print(find_missing_num(arr))
