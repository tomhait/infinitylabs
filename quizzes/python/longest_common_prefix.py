def lcp(str_list: list):
    str_list.sort(key=lambda x: len(x))
    min_s = str_list[0]
    ret = ''
    for i in range(len(min_s)):
        c = min_s[i]
        flag = True
        for s in str_list[1:]:
            if c != s[i]:
                flag = False
                break
        if flag:
            ret += c
    return ret

str_list = ["sssss", "sss", "ss"]
print(lcp(str_list))