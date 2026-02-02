import math
from numbers import Number

class Point:
    def __init__(self, x = 0.0, y = 0.0):
        self.x = x
        self.y = y
        try:
            self._is_number("x")
        except ValueError as e:
            print(e)
            self.x = 0.0
        try:
            self._is_number("y")
        except ValueError as e:
            print(e)
            self.y = 0.0

    def _is_number(self, att_name):
        value = getattr(self, att_name, None)
        if not isinstance(value, Number):
            raise ValueError(f"{att_name} is not a number, Initialized with 0.0")

    def distance(self):
        return math.sqrt(self.x**2 + self.y**2)

    def __str__(self):
        return f"Point({self.x}, {self.y})"