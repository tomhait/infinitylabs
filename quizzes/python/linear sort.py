def linear_sort(msg: list):
    counts = [0]*256
    for c in msg:
        counts[ord(c)] += 1
    sorted_c = [chr(i)*k for i,k in enumerate(counts)]
    return "".join(sorted_c)

msg = "pppaaannnmmm"
print(linear_sort(msg))