pairs = {')': '(', ']': '[', '}': '{'}

# def rec_helper(s):
#     if len(s) == 0: return True
#     # if len(s) == 1: return False
#     # if len(s) == 2:
#     #     if s[0] == s[-1]: return True
#     #     return False
#     # if s[0] == s[-1]: return rec_helper(s[1:len(s)-1])
#     # return rec_helper(s[:len(s)-1])
#     if s[0] in pairs and pairs[s[0]] == s[-1]:
#         return rec_helper(s[1:-1])
#     return False
#
# def check_parentheses(s):
#     if rec_helper(s):
#         return "Balanced"
#     return "Not Balanced"

def check_parentheses(s):
    to_match = []

    for c in s:
        if c in "([{":
            to_match.append(c)
        elif c in ")]}":
            if len(to_match) == 0 or to_match[-1] != pairs[c]:
                return "Not Balanced"
            to_match.pop()
        # if len(to_match) != 0:
        #     elem = to_match.pop()
        # else: elem = "$"
        # if pairs[c] != elem: return "Not Balanced"
        # to_match.append(c)

    if len(to_match) == 0: return "Balanced"
    return "Not Balanced"

if __name__ == "__main__":
    s = "()"
    print(check_parentheses(s))
    s = "("
    print(check_parentheses(s))
    s = "[()](){[()]()}"
    print(check_parentheses(s))
    s = "[{}(})"
    print(check_parentheses(s))