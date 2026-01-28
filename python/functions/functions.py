from functools import reduce

def remove_words(lst, *args):
    """ Removes words (defined in args) from the list"""
    return list(filter(lambda x: x not in args, lst))

def sort_str_nums(lst):
    """ Sorts list of string numbers numerically"""
    lst.sort(key=lambda x: int(x))

def sum_nums(lst):
    pass

def get_square_from_even(lst):
    return [i**2 for i in lst if i % 2 == 0]

def set_discount(dct_products, discount = 0.9):
    return {product: price*discount for product, price in dct_products.items()}

def get_hebrew_gematria(word):
    letters = "אבגדהוזחטיכלמנסעפצקרשתךםןףץ"
    word = word.replace(" ", "")
    char_to_val = {}
    for i, char in enumerate(letters):
        if i < 9:
            val = i + 1
        elif i < 18:
            val = (i - 8) * 10
        else:
            val = (i - 17) * 100
        char_to_val[char] = val
    return sum([char_to_val[x] for x in word])
