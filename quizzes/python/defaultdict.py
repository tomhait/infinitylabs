class DefaultDict(dict):
    def __init__(self, default):
        super().__init__()
        self.default = default

    def __getitem__(self, key):
        if key not in self:
            return self.default
        return super().__getitem__(key)

class DefaultDict2:
    def __init__(self, default):
        self.default = default
        self.dct = dict()

    def __getitem__(self, key):
        if key not in self.dct:
            return self.default
        return self.dct[key]

    def __setitem__(self, key, value):
        self.dct[key] = value

if __name__ == "__main__":
    dd = DefaultDict2(3)
    dd[1] = "hello"
    print(dd[1])
    print(dd[2])