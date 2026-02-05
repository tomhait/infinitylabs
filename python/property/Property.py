class Property:
    """
    Descriptor class emulation
    """
    def __init__(self, fget = None, fset = None, fdel = None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel

    def __get__(self, instance, owner):
        """ Get decorator"""
        if instance is None:
            return self
        if self.fdel is None:
            raise AttributeError("Unable to get attribute")
        return self.fget(instance)

    def __set__(self, instance, value):
        """ set decorator"""
        if not isinstance(value, int):
            raise TypeError(f"Value must be integer, not {type(value)}")
        if self.fset is None:
            raise AttributeError("Unable to set attribute")
        self.fset(instance, value)

    def __delete__(self, instance):
        """ delete decorator"""
        if self.fdel is None:
            raise AttributeError("Unable to delete attribute")
        self.fdel(instance)

    def Setter(self, fset):
        """ Setter decorator"""
        return type(self)(self.fget, fset, self.fdel)

    def Deleter(self, fdel):
        """ Setter decorator"""
        return type(self)(self.fget, self.fset, fdel)

class X:

    def __init__(self, val):
        self.__x = val

    @Property
    def x(self):
        return self.__x

    @x.Setter
    def x(self, val):
        self.__x = int(val)

    @x.Deleter
    def x(self):
        del self.__x

if __name__ == "__main__":
    a = X(0)
    print(a.x)
    a.x = 1
    print(a.x)
    del(a.x)