import math
from numbers import Number

class Point:
    """
    Represents a 2D point.
    Raise TypeError if given attributes are not numbers
    Default point values are 0.0, 0.0
    """
    def __init__(self, x = 0.0, y = 0.0):
        """ Constructor for Point class"""
        self.x = x
        self.y = y

    @property
    def x(self):
        return self.__x

    @x.setter
    def x(self, value):
        if not isinstance(value, (int, float)):
            raise TypeError("x must be a number")
        self.__x = value

    @property
    def y(self):
        return self.__y

    @y.setter
    def y(self, value):
        if not isinstance(value, (int, float)):
            raise TypeError("y must be a number")
        self.__y = value

    def __str__(self):
        """ Human-Friendly Point representation"""
        return f"Point({self.x}, {self.y})"

if __name__ == "__main__":
    p1 = Point()
    p2 = Point(2,4)
    try:
        p1.x = "Hello"
    except TypeError as e:
        print(e)
    print(p1)
    print(p2)
    p1.x = 3
    print(p1)
    help(Point)
