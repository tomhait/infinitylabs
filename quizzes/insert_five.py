def insert_five(num, replace = 5):
    ind_pos = 0
    flag = False
    str_num = str(num)
    for i, digit in enumerate(str_num):
        if replace > int(digit):
            ind_pos = i
            flag = True
            break
    if flag:
        ret_str = str_num[:ind_pos] + str(replace) + str_num[ind_pos+1:]
    else:
        ret_str = str_num
    return int(ret_str)

print(insert_five(123))
print(insert_five(523))
print(insert_five(321))
print(insert_five(3))