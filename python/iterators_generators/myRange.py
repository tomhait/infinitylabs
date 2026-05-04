
class MyRange:
    def __init__(self,*args):
        self.start = 0
        self.step = 1
        if len(args) == 1:
            self.stop = args[0]
        elif len(args) == 2:
            self.start = args[0]
            self.stop = args[1]
        else:
            self.start = args[0]
            self.stop = args[1]
            self.step = args[2]

        for val in [self.start, self.stop, self.step]:
            if not isinstance(val, int):
                raise TypeError('Not integer type')

        self.gen = self._get_next()

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.gen)

    def _get_next(self):
        yield from range(self.start, self.stop, self.step)

    def __len__(self):
        return (self.stop - self.start + self.step - 1) // self.step

range_4 = MyRange(4)
for i in range_4:
    print(i)

# print(len(range_4))
print("\n\n")

for i in MyRange(2,10):
    print(i)

print("\n\n")

for i in MyRange(2,10, 2):
    print(i)

print("\n\n")
print(len(MyRange(2,10, 2)))
