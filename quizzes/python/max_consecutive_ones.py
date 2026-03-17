def max_cons_ones(arr, N):
    left = 0

    for right in range(len(arr)):
        if arr[right] == 0:
            N -= 1

        if N < 0:
            if arr[left] == 0:
                N += 1
            left += 1

    return len(arr) - left

arr = [1,0,1,1,0,1,0,1,1,0,1,0,0]
print(max_cons_ones(arr,2))