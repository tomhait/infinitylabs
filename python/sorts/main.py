from sorts import *

if __name__ == "__main__":
    arr = [4, 2, 1, 8, 3, 3]
    print(bubble_sort([4, 2, 1, 8, 3, 3]))
    print(selection_sort([4, 2, 1, 8, 3, 3]))
    print(insertion_sort([4, 2, 1, 8, 3, 3]))
    print(merge_sort([4, 2, 1, 8, 3, 3]))
    quick_sort(arr, 0, len(arr) - 1)
    print(arr)
    arr = [4, 2, 1, 8, 3, 3]
    print(counting_sort(arr))
    arr = [170, 45, 75, 90, 802, 24, 2, 66]
    print(radix_sort(arr))