import re

def count_char_in_string(string, char):
    """ Count the number of occurrences of char in string"""
    count = 0
    for c in string:
        if c == char:
            count += 1
    return count

def flip_number(number):
    """ Reverse the order of digits in number"""
    reversed_number = 0
    sign = 1
    if number < 0:
        number = -number
        sign = -1
    while number > 0:
        reversed_number = (reversed_number * 10) + (number % 10)
        number //= 10
    return sign * reversed_number

def celcius_to_fahrenheit(celcius):
    """ Convert Celcius to Fahrenheit"""
    return (celcius * 9 / 5) + 32

def is_leap_year(year):
    """ Check if year is a leap year"""
    return (year % 4 ==0 and year % 100 != 0) or (year % 400 ==0)

def check_password(password):
    """ Check validity of a password"""
    has_lower = re.search(r'[a-z]', password) is not None
    has_upper = re.search(r'[A-Z]', password) is not None
    has_digits = re.search(r'[0-9]', password) is not None
    has_special = re.search(r'[@#%&]', password) is not None
    return has_lower and has_upper and has_digits \
        and has_special and len(password) >= 8

def sum_divisors(number):
    """ Sum the divisors of the number"""
    sum_div = 1
    if number == 1:
        return sum_div
    for div in range(2, number//2 + 1):
        if number % div ==0:
            sum_div += div
    return sum_div + number

def min_bills_and_coins(amount):
    """ Returns the minimum number of bills and
    coins that sum up to amount
    """
    count = 0
    numbers = [200, 100, 50, 20, 10, 5, 2, 1]
    if amount == 0:
        return count
    for div in numbers:
        while amount >= div:
            count += 1
            amount -= div
    return count

def is_prime(number):
    """ Checks if number is prime"""
    if number < 2:
        return False
    if sum_divisors(number) == 1 + number:
        return True
    return False
