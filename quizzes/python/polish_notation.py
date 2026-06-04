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

def eval_polish(str_pol: str):
    tokens = str_pol.split()
    stack = []
    for token in reversed(tokens):
        if is_integer(token):
            stack.append(int(token))
        else:
            op1 = stack.pop()
            op2 = stack.pop()
            if token == '+':
                res = op1 + op2
            elif token == '-':
                res = op1 - op2
            elif token == '*':
                res = op1 * op2
            else:
                res = op1 // op2
            stack.append(res)
    return stack[0]


str_pol = '+ 3 * -2 -3'
print(str_pol,'=',eval_polish(str_pol))
str_pol = '+ 3 + 4 * 7 9'
print(str_pol,'=',eval_polish(str_pol))
str_pol = '+ 5 6'
print(str_pol,'=',eval_polish(str_pol))
str_pol = '+ * + 1 2 3 4'
print(str_pol,'=',eval_polish(str_pol))