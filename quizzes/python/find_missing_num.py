import numpy as np

def find_missing_num(arr: np.ndarray):
    n = len(arr)
    tot_sum = n*(n+1)/2
    return tot_sum - np.sum(arr)

arr = np.array([0,1,4,3])
print(find_missing_num(arr))
