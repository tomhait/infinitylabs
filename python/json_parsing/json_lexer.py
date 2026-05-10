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
        ('STRING', r'"[^"]*"'),
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
                raise RuntimeError(f'Unexpected character: {value}')
            if obType in ['LBRACE', 'RBRACE', 'COLON', 'COMMA']:
                value = ""
            if obType == "STRING":
                value = value.strip('"')
            yield Token(obType, value)

if __name__ == '__main__':
    json_str = '{"name": "Tom", "age": 30, "city": "New York"}'
    lexer = JsonLexer()
    for token in lexer.tokenize(json_str):
        print(token)