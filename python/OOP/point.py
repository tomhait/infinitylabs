import math
from numbers import Number

class Point:
    """
    Represents a 2D point.
    Raise ValueError if given attributes are not numbers
    Default point values are 0.0, 0.0
    """
    def __init__(self, x = 0.0, y = 0.0):
        """ Constructor for Point class"""
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
        """ Tests if given attribute is a number"""
        value = getattr(self, att_name, None)
        if not isinstance(value, Number):
            raise ValueError(f"{att_name} is not a number, Initialized with 0.0")

    def distance(self):
        """ Returns Euclidean distance from origin"""
        return math.sqrt(self.x**2 + self.y**2)

    def __str__(self):
        """ Human-Friendly Point representation"""
        return f"Point({self.x}, {self.y})"