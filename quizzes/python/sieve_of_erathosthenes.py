from math import sqrt

def all_primes(n):
    arr = [True]*(n+1)
    arr[0] = arr[1] = False
    ret = []
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

print(all_primes(20))