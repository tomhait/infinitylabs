import time

def InfiniteRange():
    i = 0
    while True:
        yield i
        i+=1

# a = InfiniteRange()
# for i in a:
#     print(i)
#     time.sleep(0.5)

a = (i for i in InfiniteRange() if i%2 == 0)
for i in a:
    print(i)
    time.sleep(0.5)