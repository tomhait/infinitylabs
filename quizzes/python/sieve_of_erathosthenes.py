from math import sqrt
import time
import numpy as np


def all_primes(n):
    arr = [True]*(n+1)
    arr[0] = arr[1] = False
    up_to = int(sqrt(n))

    for k in range(2, up_to + 1):
        if not arr[k]:
            continue
        p = k*k
        while p <= n:
            arr[p] = False
            p += k

    ret = [k for k, is_prime in enumerate(arr) if is_prime]
    return ret

def all_primes_numpy(n):
    primes = np.ones(n+1,dtype=np.bool)
    primes[:2] = False
    up_to = int(np.sqrt(n))

    for k in range(2, up_to + 1):
        if primes[k]:
            primes[k*k:n:k] = False

    return np.nonzero(primes)[0]

start = time.perf_counter()
all_primes_numpy(10_000_000_000)
end = time.perf_counter()
print(end-start)