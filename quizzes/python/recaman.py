seq = set()
def recaman():
    n = 0
    current = -1
    while True:
        if n == 0:
            current = 0
            seq.add(n)
            n += 1
            yield current
        val = current - n
        if val in seq or val < 0:
            val = current + n
        n += 1
        seq.add(val)
        current = val
        yield val

gen = recaman()
for i in range(16):
    print(f"{i}:{next(gen)}")

