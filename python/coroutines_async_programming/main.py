from scheduler import *

def test1():
    pq = PriorityQueue()
    for i in range(5):
        pq.push(i)
    assert pq.peek() == 0
    assert pq.pop() == 0
    assert pq.peek() == 1
    assert len(pq) == 4
    pq.push(-1)
    assert pq.peek() == -1

def test2():
    def hello():
        print('Hello')
        print(f'current time: {time.time()}')

    sched = Scheduler()
    start_time = time.time()
    sched.add(start_time + 1, hello)
    sched.add(start_time + 2, hello)
    sched.run()

def test3():
    pings = 5
    def ping():
        nonlocal pings
        pings -= 1
        print(f'Ping {pings} at: {time.time():.0f}')
        if pings != 0: return True
        return False
    sched = FreqScheduler()
    sched.add(time.time(), ping, freq=2)
    sched.run()

def test4():
    pings = 5
    def ping():
        nonlocal pings
        while pings:
            pings -= 1
            print(f'Ping {pings} at: {time.time():.0f}')
            yield pings

    sched = CoroScheduler()
    sched.add(time.time(), ping(), freq=2)
    sched.run()

def test5():
    seconds = 5
    def ping():
        nonlocal seconds
        while seconds:
            seconds -= 1
            print(f'Ping {seconds} at: {time.time():.0f}')
            yield seconds

    sched = FlexCoroScheduler()
    sched.add(time.time(), ping(), 0)
    sched.run()

def test6():
    def mix_task1():
        print("\n")
        for i in range(10):
            if i%2 == 0:
                print(f"{i} is even, taking a 2 sec nap..., time: {time.time():.0f}")
                yield 2
            else:
                print(f"{i} is odd, continue executing..., time: {time.time():.0f}")
                yield

    def mix_task2():
        print("\n")
        for i in range(13):
            if i%3 == 0:
                print(f"{i} divides 3, continue executing..., time: {time.time():.0f}")
                yield
            else:
                print(f"{i} doesn't divides 3, taking a 2 sec nap..., time: {time.time():.0f}")
                yield 2

    sched = MixScheduler()
    sched.add(mix_task1())
    sched.add(mix_task2())
    sched.run()

def test7():
    async def my_task(name, duration):
        print(f"\nTask {name} started...")
        await Sleep(duration)
        print(f"Task {name} woke up after {duration}s!")

    sched = SleepScheduler()
    sched.add(my_task("A", 2))
    sched.add(my_task("B", 1))
    sched.add(my_task("C", 0.5))
    sched.run()