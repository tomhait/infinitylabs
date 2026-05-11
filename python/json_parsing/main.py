from json_lexer import *
import json
import os
import pytest

base_path = os.path.dirname(__file__)
lexer = JsonLexer()
json_parser = MyJsonParser()

def test1():
    array_str = '[[["name", "age"]], "Tom", 30]'
    print("\n",json_parser.parse_array(lexer.tokenize(array_str)))
    assert json_parser.parse_array(lexer.tokenize(array_str)) == [[['name', 'age']], 'Tom', 30]

def test2():
    file_path = os.path.join(base_path, 'json_complex.json')
    with open(file_path, 'r') as f:
        obj_str = f.read()
        data = json_parser.loads(obj_str)
        print("\n",data)
        assert data == json.loads(obj_str)

def test3():
    obj_str = '{"key":1}s'
    with pytest.raises(ValueError):
        data = json_parser.loads(obj_str)

def test4():
    obj_str = '{"key":]}'
    with pytest.raises(ValueError):
        data = json_parser.loads(obj_str)

def test5():
    obj_str = '{"key":}'
    with pytest.raises(ValueError):
        data = json_parser.loads(obj_str)

def test6():
    obj_str = '{"key": True}'
    with pytest.raises(ValueError):
        data = json_parser.loads(obj_str)

def test7():
    obj_str = '{"key": [}'
    with pytest.raises(ValueError):
        data = json_parser.loads(obj_str)

def test8():
    obj_str = '"s"'
    with pytest.raises(ValueError):
        data = json_parser.loads(obj_str)




