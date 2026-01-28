from functools import reduce

def remove_words(lst, *args):
    """ Removes words (defined in args) from the list"""
    return list(filter(lambda x: x not in args, lst))

def sort_str_nums(lst):
    """ Sorts list of string numbers numerically"""
    lst.sort(key=lambda x: x)

def sum_neg_pos_nums(lst):
    """ Returns a tuple where the first (second)
     variable is the sum of positive (negative)
     elements in lst, respectively
     """
    pos_sum = sum([x for x in lst if x > 0])
    neg_sum = sum([x for x in lst if x < 0])
    return pos_sum, neg_sum

def get_square_from_even(lst):
    """ Returns a list of squared
    even elements in the list
    """
    return [i**2 for i in lst if i % 2 == 0]

def set_discount(dct_products, discount = 0.9):
    """ Returns a new dictionary with
    discounted prices for every product
    """
    return {product: price*discount for product, price in dct_products.items()}

def create_gematria_table():
    """ Creates a wrapper function to compute
    the gematria value of a hebrew letter
    """
    letters = "אבגדהוזחטיכלמנסעפצקרשתךםןףץ"
    char_to_val = {}
    for i, char in enumerate(letters):
        if i < 9:
            val = i + 1
        elif i < 18:
            val = (i - 8) * 10
        else:
            val = (i - 17) * 100
        char_to_val[char] = val
    def get_gematria_val(c):
        return char_to_val[c]
    return get_gematria_val

def get_hebrew_gematria(word):
    """ Returns the hebrew
    gematria number of the word
    """
    word = word.replace(" ", "")
    gematria_tab = create_gematria_table()
    return sum([gematria_tab(x) for x in word])

def check_credit_card(card_num):
    """ Test credit card validity using
    the Luhn algorithm
    """
    card_num = str(card_num)[::-1]
    tot_sum = 0
    for i, digit in enumerate(card_num):
        if i % 2 != 0:
            prod = int(digit) * 2
            if prod > 9:
                prod -= 9
            tot_sum += prod
        else:
            tot_sum += int(digit)
    if tot_sum % 10 == 0:
        return True
    return False

