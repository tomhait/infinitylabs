import sys
import pytest
import python_intro

def test_char_count():
    assert(python_intro.count_char_in_string("blablabla", 'a') == 3)

def test_flip():
    assert(python_intro.flip_number(1234) == 4321)

def test_degree_conversion():
    assert(python_intro.celcius_to_fahrenheit(24) == 75.2)

def test_is_leap_year():
    assert(python_intro.is_leap_year(2020) is True)
    assert(python_intro.is_leap_year(2000) is True)
    assert(python_intro.is_leap_year(2026) is False)

def test_check_pass():
    assert(python_intro.check_password("Tom12345#") == True)
    assert(python_intro.check_password("tom12345#") == False)

def test_sum_divisors():
    assert(python_intro.sum_divisors(10) == 18)

def test_count_bills():
    assert(python_intro.min_bills_and_coins(105) == 2)

def test_is_prime():
    assert(python_intro.is_prime(105) is False)
    assert(python_intro.is_prime(13) is True)
    assert(python_intro.is_prime(31) is True)