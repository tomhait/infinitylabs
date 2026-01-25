
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
    while number > 0:
        reversed_number = (reversed_number * 10) + (number % 10)
        number //= 10
    return reversed_number

def celcius_to_fahrenheit(celcius):
    """ Convert Celcius to Fahrenheit"""
    return (celcius * 9 / 5) + 32

