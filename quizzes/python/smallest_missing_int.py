def smallest_missing(arr: list):
    if not arr or arr[0] != 0:
        return 0
    left, right = 0, len(arr) - 1

    while left <= right:
        mid = left + (right - left) // 2

        if arr[mid] != mid:
            right = mid - 1
        else:
            left = mid + 1
    return left

arr = [0, 1, 3, 4, 6, 1984]
print(smallest_missing(arr))

arr = [0, 1, 2, 3, 4, 6, 1984]
print(smallest_missing(arr))
