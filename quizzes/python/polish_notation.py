from collections import deque

def calc_polish(str_pol: str):
    ops = deque()
    nums = deque()
    str_pol = str_pol.split()
    for c in str_pol:
        if is_integer(c):
            nums.append(c)
        else:
            ops.append(c)
    str_eq = nums.popleft()
    while ops:
        op = ops.popleft()
        num = nums.popleft()
        str_eq = num + op + str_eq
    return eval(str_eq)

def is_integer(val):
    try:
        int(val)
        return True
    except ValueError:
        return False

str_pol = '+ 3 * -2 -3'
print(str_pol,'=',calc_polish(str_pol))