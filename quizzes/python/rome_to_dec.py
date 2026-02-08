def rome_to_dec(rome_num):
    conv_dct = {'I': 1, "V": 5, "X": 10, "L": 50,
                "C": 100, "D": 500, "M": 1000}

    if len(rome_num) == 1:
        return conv_dct.get(rome_num, 0)

    i = 0
    result = 0
    while i < len(rome_num) - 1:
        first = conv_dct.get(rome_num[i],0)
        second = conv_dct.get(rome_num[i+1], 0)

        if second <= first:
            result += first
        else:
            result -= first
        i += 1

    result += conv_dct.get(rome_num[-1], 0)
    return result

print(rome_to_dec("MCMXCIV"))
print(rome_to_dec("XXX"))