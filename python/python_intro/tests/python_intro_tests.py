import sys
import pytest

from python_intro import *

def test_char_count():
    assert(count_char_in_string("blablabla", 'a') == 3)

def test_flip():
    assert(flip_number(1234) == 4321)

def test_degree_conversion():
    assert(celcius_to_fahrenheit(24) == 75.2)

def test_is_leap_year():
    assert(is_leap_year(2020) is True)
    assert(is_leap_year(2000) is True)
    assert(is_leap_year(2026) is False)

def test_check_pass():
    assert(check_password("Tom12345#") == True)
    assert(check_password("tom12345#") == False)

def test_sum_divisors():
    assert(sum_divisors(10) == 18)
    assert (sum_divisors(1) == 1)

def test_count_bills():
    assert(min_bills_and_coins(105) == 2)

def test_is_prime():
    assert(is_prime(105) is False)
    assert (is_prime(0) is False)
    assert(is_prime(13) is True)
    assert(is_prime(31) is True)
    assert (is_prime(1) is False)