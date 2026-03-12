def find_ind(arr, elem, first = True):
    ret = -1
    n = len(arr)
    left, right = 0, n-1

    while left <= right:
        mid = left + (right - left) // 2
        if arr[mid] == elem:
            ret = mid
            if first:
                right = mid - 1
            else:
                left = mid + 1
        elif arr[mid] < elem:
            left = mid + 1
        else:
            right = mid - 1
    return ret

def find_range(arr, elem):
    if not arr:
        return -1, -1
    n = len(arr)
    if n == 1:
        if arr[0] == elem:
            return 0, 0
        else:
            return -1, -1
    return find_ind(arr, elem), find_ind(arr, elem, False)

arr = [1, 4, 6, 6, 6, 12]
print(find_range(arr, 6))

arr = [1]
print(find_range(arr, 1))

arr = [0,1]
print(find_range(arr, 1))

arr = [0]
print(find_range(arr, 1))