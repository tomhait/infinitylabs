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

def test_left_rotation():
    list1 = [1, 2, 3, 4]
    assert(left_rotate_list(list1) == [2, 3, 4, 1])

def test_print_and_remove_second():
    list1 = [1, 2, 3, 4, 5, 6, 7, 8]
    print_and_remove(list1)

def test_dict_to_tuples_list():
    dict1 = {"Tom": 1, "Danny": 2, "Gabi": 3}
    list1 = convert_dict_to_tuples(dict1)
    assert(list1[0] == ("Tom", 1))
    assert (list1[1] != ("Danny", 1))

def test_max_min_dict():
    dict1 = {"Tom": 1, "Danny": 2, "Gabi": 3}
    get_max_min_keys(dict1)

def test_diff_str():
    s1 = 'lorem ipsum'
    s2 = 'lmnop'
    assert(get_diff_str(s1, s2) == 're isu')
