
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
    unique_list = list(dict.fromkeys([x for x in list1 if x in list2]))
    return unique_list

def get_unique_dict_values(dict1):
    """ Returns a list with unique values in dictionary"""
    return list(dict.fromkeys(dict1.values()))


