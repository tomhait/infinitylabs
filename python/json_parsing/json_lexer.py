import re
from dataclasses import dataclass
from typing import Any

@dataclass
class Token:
    obType: str
    value: Any

class JsonLexer:
    rules = [
        ('NUMBER', r'[+-]?\d+(\.\d+)?'),
        ('STRING', r'\"[^"\\]*\"|\'[^\'\\]*\''),
        ('LBRACE', r'\{'),
        ('RBRACE', r'\}'),
        ('LBRACKET', r'\['),
        ('RBRACKET', r'\]'),
        ('COLON', r':'),
        ('COMMA', r','),
        ('BOOL', r'True|False|true|false'),
        ('NULL', r'null'),
        ('SKIP', r'[ \t\n\r]+'),
        ('MISMATCH', r'.'),
    ]
    regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in rules)

    def tokenize(self, text: str):
        for match in re.finditer(self.regex, text):
            obType = match.lastgroup
            value = match.group()
            if obType == 'SKIP':
                continue
            elif obType == 'MISMATCH':
                raise RuntimeError(f'Unexpected character: {value}')
            if obType in ['LBRACE', 'RBRACE', 'COLON', 'COMMA']:
                value = ""
            if obType == "STRING":
                value = value[1:-1]
            yield Token(obType, value)

def cast_to_type(token):
    if token.obType == 'STRING':
        return token.value
    if token.obType == 'NUMBER':
        return int(token.value)
    return True if token.value.lower() == 'true' else False

def parse_array(tokens_gen):
    token = next(tokens_gen)
    if token.obType != 'LBRACKET':
        raise ValueError("Expected '[' at the start of the array")
    result = []
    while True:
        token = next(tokens_gen)
        if token.obType == 'RBRACKET':
            return result
        if token.obType in ('STRING', 'NUMBER', 'BOOL'):
            result.append(cast_to_type(token))
        else:
            raise ValueError(f"Unexpected token {token.obType}")
        token = next(tokens_gen)
        if token.obType == 'RBRACKET':
            return result
        elif token.obType != 'COMMA':
            raise ValueError("Expected ',' between array elements")

def parse_object(tokens_gen):
    token = next(tokens_gen)
    if token.obType != 'LBRACE':
        raise ValueError("Expected '{' at the start of the array")
    result = {}
    while True:
        token = next(tokens_gen)
        if token.obType == 'RBRACE':
            return result

        if token.obType != 'STRING':
            raise ValueError('Key should be a string')

        key = token.value
        token = next(tokens_gen)
        if token.obType != 'COLON':
            raise ValueError("Expected ':' between key-value pair")

        token = next(tokens_gen)
        if token.obType in ('STRING', 'NUMBER', 'BOOL'):
            if key not in result:
                result[key] = []
            result[key].append(cast_to_type(token))
        else:
            raise ValueError(f"Unexpected token {token.obType}")

        token = next(tokens_gen)
        if token.obType == 'RBRACE':
            return result
        elif token.obType != 'COMMA':
            raise ValueError("Expected ',' between array elements")

if __name__ == '__main__':
    json_str = '{"name": "Tom", "age": 30, "city": "New York"}'
    lexer = JsonLexer()
    for token in lexer.tokenize(json_str):
        print(token)

    array_str = '["name", "age", "Tom", 30]'
    print(parse_array(lexer.tokenize(array_str)))
    assert parse_array(lexer.tokenize(array_str)) == ['name', 'age', 'Tom', 30]

    obj_str = "{'name': 'Tom', 'name': 'Gabbi', 'age': 30, 'age': 32, 'is_ok': True}"
    print(parse_object(lexer.tokenize(obj_str)))