
def remove_non_str(list_arr):
    """ Removes non str objects from the list"""
    list_copy = list_arr[:]
    for x in list_copy:
        if not isinstance(x, str):
            list_arr.remove(x)

def dict_char_counter(s):
    """ Returns a dictionary with unique chars in s as keys
    and their values as the number of times each char appears in s
    """
    chars = set(s)
    char_dict = {x: s.count(x) for x in chars}
    return char_dict

def intersect_unique_elem_lists(list1, list2):
    """ Returns a new list containing elements that appear
    in both lists
    """
    return list(dict.fromkeys([x for x in list1 if x in list2]))

def get_unique_dict_values(dict1):
    """ Returns a list with unique values in dictionary"""
    return list(dict.fromkeys(dict1.values()))

def left_rotate_list(list1):
    """ Left rotation of a list"""
    return list1[1:] + list1[:1]

def print_and_remove(list1):
    """ Prints and removes every second element
    until the list is empty
    """
    index = 1
    while list1:
        index %= len(list1)
        print(list1.pop(index))
        index += 1

def convert_dict_to_tuples(dict1):
    """ Converts a dictionary to a list of tuples"""
    return list(dict1.items())

def get_max_min_keys(dict1):
    """ Prints the keys of the maximum and minimum
    values in a dictionary
    """
    list1 = convert_dict_to_tuples(dict1)
    max_key = max(list1, key=lambda x: x[1])[0]
    min_key = min(list1, key=lambda x: x[1])[0]
    print("max key: " + max_key)
    print("min key: " + min_key)

def get_diff_str(s1, s2):
    """ Returns substring of letters in s1 (n) that don't
    appear in s2 (m) in O(n+m) time complexity
    """
    dict1 = {x: 0 for x in s2}
    return ''.join([x for x in s1 if x not in dict1])