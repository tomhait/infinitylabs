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
    errors = {
        'RBRACKET': "Expected '[' at the start of the array",
        'LBRACE': "Expected '{' at the start of the array",
        'COLON': "Expected ':' between key-value pair"
    }
    def _cast_to_type(self, token):
        if token.obType == 'STRING':
            return token.value
        if token.obType == 'NUMBER':
            if any(item in token.value for item in ('.','e','E')):
                return float(token.value)
            return int(token.value)
        return True if token.value.lower() == 'true' else False

    def _parse_value(self, tokens_gen, token = None):
        if not token: token = next(tokens_gen)
        if token.obType in ('STRING', 'NUMBER', 'BOOL'):
            return self._cast_to_type(token)
        elif token.obType == 'LBRACKET':
            return self.parse_array(tokens_gen, is_nested=True)
        elif token.obType == 'LBRACE':
            return self.parse_object(tokens_gen, is_nested=True)
        else:
            raise ValueError(f"Unexpected token {token.obType}")

    def _is_enclosing(self, tokens_gen, enclosingType ='RBRACKET'):
        token = next(tokens_gen)
        if token.obType == enclosingType:
            return True
        elif token.obType != 'COMMA':
            raise ValueError("Expected ',' between array elements")
        return False

    def _consume_token(self, tokens_gen, tokenType = 'LBRACKET'):
        token = next(tokens_gen)
        if token.obType != tokenType:
            raise ValueError(self.errors[tokenType])

    def parse_array(self, tokens_gen, is_nested = False):
        if not is_nested:
            self._consume_token(tokens_gen, tokenType = 'LBRACKET')
        result = []
        while True:
            token = next(tokens_gen)
            if token.obType == 'RBRACKET':
                return result
            result.append(self._parse_value(tokens_gen,token))
            if self._is_enclosing(tokens_gen):
                return result

    def parse_object(self, tokens_gen, is_nested = False):
        if not is_nested:
            self._consume_token(tokens_gen, tokenType = 'LBRACE')
        result = {}
        while True:
            token = next(tokens_gen)
            if token.obType == 'RBRACE':
                return result

            if token.obType != 'STRING':
                raise ValueError('Key should be a string')

            key = token.value
            self._consume_token(tokens_gen, tokenType = 'COLON')

            result[key] = self._parse_value(tokens_gen)

            if self._is_enclosing(tokens_gen, enclosingType='RBRACE'):
                return result

    def loads(self, obj_str):
        tokens_gen = self.lexer.tokenize(obj_str)
        data = self.parse_object(tokens_gen)
        is_end = next(tokens_gen, 'END')
        if is_end == 'END':
            return data
        raise ValueError(f"JSON object is not built correctly: {is_end}")

