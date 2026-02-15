import string

def is_pangram(s):
    let_lst = [c for c in string.ascii_uppercase]

    for c in s:
        c_up = c.upper()
        if c_up in let_lst:
            let_lst.remove(c_up)
        if not let_lst:
            return True
    if not let_lst:
        return True
    return False

if __name__=="__main__":
    s = "The quick brown fox jumps over the lazy dog"
    print(is_pangram(s))
    print(is_pangram("bla"))
