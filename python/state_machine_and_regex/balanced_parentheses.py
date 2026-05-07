import regex

def is_balanced(text: str):
    pattern = r"[^()]*(\((?:(?R)|[^()]*)*\)[^()]*)*"
    return bool(regex.fullmatch(pattern, text))

if __name__=='__main__':
    print(f'(bn(())): {is_balanced('(bn(()))')}')
    print(f'(bn()))): {is_balanced('(bn())))')}')
    print(f'(bn(dd(mn))): {is_balanced('(bn(dd(mn)))')}')
    print(f'aaa(((1+0)+1)+1)bbb: {is_balanced('aaa(((1+0)+1)+1)bbb')}')
