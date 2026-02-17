import numpy as np
from datetime import datetime
from functools import wraps
import math

def func_timer(func):
    @wraps(func)
    def wrap_func(*args, **kargs):
        start = datetime.now()
        res = func(*args, **kargs)
        time_elapsed = (datetime.now() - start).total_seconds()
        print(f"The {func.__name__} took {time_elapsed} seconds")
        return res
    return wrap_func

@func_timer
def zero_list(n):
    return [0]*n

@func_timer
def zero_np(n):
    return np.zeros(n)

@func_timer
def add_const(arr: np.ndarray | list, val = 5):
    if isinstance(arr, list):
        return [x + val for x in arr]
    return arr + val

@func_timer
def dot_prod(arr1: np.ndarray | list, arr2: np.ndarray | list):
    if isinstance(arr1, list):
        return [arr2[i] * x for i, x in enumerate(arr1)]
    return arr1.dot(arr2)

@func_timer
def apply_exp(arr: np.ndarray | list):
    if isinstance(arr, list):
        return [math.exp(x) for x in arr]
    return np.exp(arr)

@func_timer
def concat(arr1: np.ndarray | list, arr2: np.ndarray | list):
    if isinstance(arr1, list):
        return arr1 + arr2
    return np.concatenate((arr1,arr2))

@func_timer
def print_elem(arr: np.ndarray | list):
    print(arr)

n=10000000
a_list = zero_list(n)
a_np = zero_np(n)

a_list1 = add_const(a_list, val = 1)
a_list2 = add_const(a_list)
a_np1 = add_const(a_np, val = 1)
a_np2 = add_const(a_np)

dot_prod(a_list1, a_list2)
dot_prod(a_np1, a_np2)

apply_exp(a_list1)
apply_exp(a_np1)

concat(a_list1, a_list2)
concat(a_np1, a_np2)

print_elem(a_list1)
print_elem(a_np1)