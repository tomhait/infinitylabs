class MyRange:
    def __init__(self, *args):
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

    def __getitem__(self, index):
        if not isinstance(index, int):
            raise TypeError('Index should be integer')

        if index < 0:
            index += len(self)

        if index < 0 or index >= len(self):
            raise IndexError("MyRange index out of range")

        return self.start + (index * self.step)

    def __len__(self):
        step = self.step if self.step > 0 else (-1) * self.step
        return max(0,(self.stop - self.start + step - 1) // step)

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

print(len(MyRange(2,10, -1)))
print(len(MyRange(5, 1)))
print(len(MyRange(2,10, 2)))

print("\n\n")
r = MyRange(2, 100)
print(r[14]) # should be 16
print(r[-1]) # should be 99
print(len(r))
print(r[130]) # IndexError