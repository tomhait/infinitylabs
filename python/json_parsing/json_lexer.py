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
        if '.' not in token.value:
            return int(token.value)
        return float(token.value)
    return True if token.value.lower() == 'true' else False

def parse_array(tokens_gen, is_nested = False):
    if not is_nested:
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
        elif token.obType == 'LBRACKET':
            result.append(parse_array(tokens_gen, is_nested=True))
        elif token.obType == 'LBRACE':
            result.append(parse_object(tokens_gen, is_nested=True))
        else:
            raise ValueError(f"Unexpected token {token.obType}")
        token = next(tokens_gen)
        if token.obType == 'RBRACKET':
            return result
        elif token.obType != 'COMMA':
            raise ValueError("Expected ',' between array elements")

def parse_object(tokens_gen, is_nested = False):
    if not is_nested:
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
            result[key] = cast_to_type(token)
        elif token.obType == 'LBRACKET':
            result[key] = parse_array(tokens_gen, is_nested=True)
        elif token.obType == 'LBRACE':
            result[key] = parse_object(tokens_gen, is_nested=True)
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

    array_str = '[[["name", "age"]], "Tom", 30]'
    print(parse_array(lexer.tokenize(array_str)))
    assert parse_array(lexer.tokenize(array_str)) == [[['name', 'age']], 'Tom', 30]

    obj_str = '''
        {
      "id": "USR-94821",
      "isActive": true,
      "profile": {
        "firstName": "John",
        "lastName": "Doe",
        "contact": {
          "email": "j.doe@example.com",
          "phone": "+1-555-010-9999",
          "address": {
            "street": "123 Tech Lane",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94105"
          }
        }
      },
      "organizations": [
        {
          "name": "CloudNine Solutions",
          "role": "Senior Architect",
          "departments": ["Engineering", "Research"],
          "projects": [
            { "id": "PRJ-01", "name": "Titan", "status": "ongoing" },
            { "id": "PRJ-02", "name": "Atlas", "status": "completed" }
          ]
        },
        {
          "name": "OpenSource Foundation",
          "role": "Contributor",
          "departments": ["Community Outsourcing"],
          "projects": []
        }
      ],
      "preferences": {
        "notifications": {
          "email": true,
          "sms": false,
          "push": true
        },
        "theme": "dark"
      },
      "metadata": {
        "lastLogin": "2024-05-10T14:30:00Z",
        "version": 2.1
      }
    }
    '''
    print(parse_object(lexer.tokenize(obj_str)))