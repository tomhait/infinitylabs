import itertools
import numpy as np

def bubble_sort(arr: list):
    """
    O(n^2) worst/average time complexity
    O(1) space complexity (in-place)
    Stable
    """
    n = len(arr)
    for i in range(n):
        is_swap = False
        for j in range(n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                is_swap = True
        if not is_swap:
            break
    return arr

def selection_sort(arr: list):
    """
    O(n^2) worst/average time complexity
    O(1) space complexity (in-place)
    Not stable
    """
    n = len(arr)
    for i in range(n):
        min_ind = min(range(i, n), key=lambda ind: arr[ind])
        arr[i], arr[min_ind] = arr[min_ind], arr[i]
    return arr

def insertion_sort(arr: list):
    """
    O(n^2) worst time complexity
    O(n) is nearly sorted
    O(1) space complexity (in-place)
    Stable
    """
    n = len(arr)
    for i in range(1, n):
        key = arr[i]
        j = i-1
        while j >= 0 and key < arr[j]:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j+1] = key
    return arr

def _merge_helper(left_arr: list, right_arr: list):
    sorted_arr = []

    while left_arr and right_arr:
        if left_arr[0] <= right_arr[0]:
            sorted_arr.append(left_arr.pop(0))
        else:
            sorted_arr.append(right_arr.pop(0))

    sorted_arr.extend(left_arr or right_arr)
    return sorted_arr


def merge_sort(arr: list):
    """
    O(n log n) worst/average time complexity
    O(n) space complexity
    Stable
    """
    if len(arr) <= 1:
        return arr

    mid = len(arr) // 2
    left_arr = merge_sort(arr[:mid])
    right_arr = merge_sort(arr[mid:])
    return _merge_helper(left_arr, right_arr)

def _partition(arr, low, high):
    """ Tony Hoare 1962 partition for quick sort"""
    pivot = arr[high]
    i = low
    for j in range(low,high):
        if arr[j] <= pivot:
            arr[i], arr[j] = arr[j], arr[i]
            i += 1
    arr[i], arr[high] = arr[high], arr[i]
    return i

def quick_sort(arr: list, low: int, high: int):
    """
    O(n^2) worst, O(n log n) average time complexity
    O(log n) space complexity (in-place - Hoare 1962)
    Not stable
    """
    if low >= high or low < 0:
        return
    p = _partition(arr, low, high)
    quick_sort(arr, low, p - 1)
    quick_sort(arr, p + 1, high)

def counting_sort(arr: list):
    """
    Non - comparison algorithm
    O(n + k) time complexity (n - num of elements, k - range of the input values)
    O(n + k) space complexity (count/output array)
    Stable
    """
    count_arr = np.bincount(arr)
    count_arr = list(itertools.accumulate(count_arr))
    sorted_arr = [0] * len(arr)
    for x in arr[::-1]:
        sorted_arr[count_arr[x]-1] = x
        count_arr[x] -= 1
    return sorted_arr






def radix_sort(lst: list):
    pass
