import pytest

from functions import *

def test_remove_words():
    words = ["Tom", "Danny", "Gabi"]
    lst = [1, 2, 3, "Tom", "Gabi", "Tom"]
    filt_lst = remove_words(lst, *words)
    assert(filt_lst == [1, 2, 3])

def test_sort_str_nums():
    lst = ["4", "5", "1", "0"]
    sort_str_nums(lst)
    assert(lst == ["0", "1", "4", "5"])

def test_sum_nums():
    pass

def test_square_from_even():
    lst = [0, 1, 2, 3, 4, 6]
    square_lst = get_square_from_even(lst)
    assert(square_lst == [0, 4, 16, 36])

def test_gematria():
    assert(get_hebrew_gematria("אינפיניטי לאבס") == 323)
    assert (get_hebrew_gematria("שלום") == 936)

def test_cred_card_check():
    assert(check_credit_card(1789372997) == False)
    assert(check_credit_card(79927398713) == True)