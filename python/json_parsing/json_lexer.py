import re
from dataclasses import dataclass
from typing import Any

@dataclass
class Token:
    obType: str
    value: Any

class JsonLexer:
    rules = [
        ('NUMBER', r'[+-]?\d+(\.\d+)?([eE][+-]?\d+)?'),
        ('STRING', r'\"[^"\\]*\"|\'[^\'\\]*\''),
        ('LBRACE', r'\{'),
        ('RBRACE', r'\}'),
        ('LBRACKET', r'\['),
        ('RBRACKET', r'\]'),
        ('COLON', r':'),
        ('COMMA', r','),
        ('BOOL', r'true|false'),
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
                raise ValueError(f'Unexpected character: {value}')
            if obType in ['LBRACE', 'RBRACE', 'COLON', 'COMMA']:
                value = ""
            if obType == "STRING":
                value = value[1:-1]
            yield Token(obType, value)

class MyJsonParser:
    lexer = JsonLexer()
    def _cast_to_type(self, token):
        if token.obType == 'STRING':
            return token.value
        if token.obType == 'NUMBER':
            if any(item in token.value for item in ('.','e','E')):
                return float(token.value)
            return int(token.value)
        return True if token.value.lower() == 'true' else False

    def parse_array(self, tokens_gen, is_nested = False):
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
                result.append(self._cast_to_type(token))
            elif token.obType == 'LBRACKET':
                result.append(self.parse_array(tokens_gen, is_nested=True))
            elif token.obType == 'LBRACE':
                result.append(self.parse_object(tokens_gen, is_nested=True))
            else:
                raise ValueError(f"Unexpected token {token.obType}")
            token = next(tokens_gen)
            if token.obType == 'RBRACKET':
                return result
            elif token.obType != 'COMMA':
                raise ValueError("Expected ',' between array elements")

    def parse_object(self, tokens_gen, is_nested = False):
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
                result[key] = self._cast_to_type(token)
            elif token.obType == 'LBRACKET':
                result[key] = self.parse_array(tokens_gen, is_nested=True)
            elif token.obType == 'LBRACE':
                result[key] = self.parse_object(tokens_gen, is_nested=True)
            else:
                raise ValueError(f"Unexpected token {token.obType}")

            token = next(tokens_gen)
            if token.obType == 'RBRACE':
                return result
            elif token.obType != 'COMMA':
                raise ValueError("Expected ',' between array elements")

    def loads(self, obj_str):
        tokens_gen = self.lexer.tokenize(obj_str)
        data = self.parse_object(tokens_gen)
        is_end = next(tokens_gen, 'END')
        if is_end == 'END':
            return data
        raise ValueError(f"JSON object is not built correctly: {is_end}")

