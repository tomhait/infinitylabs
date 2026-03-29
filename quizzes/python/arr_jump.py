def jump_arr(arr, pos=0, steps=1):
    if pos == len(arr) - 1:
        return True
    if pos < 0 or pos >= len(arr):
        return False
    if steps == len(arr):
        return False
    steps += 1
    return jump_arr(arr,pos + arr[pos], steps) or jump_arr(arr, pos - arr[pos], steps)

arr = [1,0]
print(jump_arr(arr))
