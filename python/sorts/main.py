from sorts import *

if __name__ == "__main__":
    arr = [4, 2, 1, 8, 3, 3]
    print(bubble_sort(arr[:]))
    print(selection_sort(arr[:]))
    print(insertion_sort(arr[:]))
    print(merge_sort(arr[:]))
    print(counting_sort(arr[:]))
    quick_sort(arr, 0, len(arr) - 1)
    print(arr)
    arr = [170, 45, 75, 90, 802, 24, 2, 66]
    print(radix_sort(arr))