from data_structures import *

def test_non_str_list():
    list_arr = ["Tom", 4, 6, 7, "Danny", 4.5]
    remove_non_str(list_arr)
    assert(list_arr == ["Tom", "Danny"])

def test_count_chars_dict():
    s = "blablatom"
    dict_char = dict_char_counter(s)
    assert(dict_char.get('b', 0) == 2)
    assert (dict_char.get('l', 0)== 2)
    assert (dict_char.get('a', 0) == 2)
    assert (dict_char.get('t', 0) == 1)
    assert (dict_char.get('c', 0) == 0)

def test_list_intersection():
    list1 = [1, 2, "a", "b", 4, 5, 5]
    list2 = [1, "a", 4, 5]
    assert(intersect_unique_elem_lists(list1, list2) == [1, "a", 4, 5])

def test_get_unique_dict_values():
    dict1 = {'x': 2, 'y': 1, 'c': 2}
    assert(get_unique_dict_values(dict1) == [2, 1])
