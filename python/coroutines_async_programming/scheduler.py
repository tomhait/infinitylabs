import time
from priorityQueue import PriorityQueue

class Scheduler:
    def __init__(self):
        self._pq = PriorityQueue()

    def add(self, time_point, call_task):
        self._pq.push((time_point, call_task))

    def run(self):
        print("\nScheduler started...")
        while self._pq:
            time_schedule, task = self._pq.peek()

            if time.time() >= time_schedule:
                self._pq.pop()
                task()
            else:
                time.sleep(0.1)
        print("All tasks completed")

class FreqScheduler(Scheduler):
    def add(self, time_point, call_task, freq = 0):
        self._pq.push((time_point, call_task, freq))

    def run(self):
        print("\nFrequency scheduler started...")
        while self._pq:
            time_schedule, task, freq = self._pq.peek()
            if time.time() >= time_schedule:
                self._pq.pop()
                if task() and freq:
                    self.add(time_schedule + freq, task, freq)
            else:
                time.sleep(0.1)
        print("All tasks completed")

class CoroScheduler(FreqScheduler):
    def add(self, time_point, coro, freq = 0):
        self._pq.push((time_point, coro, freq))

    def run(self):
        print("\nCoroutine scheduler started...")
        while self._pq:
            time_schedule, coro, freq = self._pq.peek()
            if time.time() >= time_schedule:
                self._pq.pop()
                try:
                    next(coro)

                    self.add(time_schedule + freq, coro, freq)
                except StopIteration:
                    print('Coroutine completed')
            else:
                time.sleep(0.1)
        print("All coroutines completed")

class FlexCoroScheduler(CoroScheduler):
    def run(self):
        print("\nFlexible coroutine scheduler started...")
        while self._pq:
            time_schedule, coro, flex_freq = self._pq.peek()
            if time.time() >= time_schedule:
                self._pq.pop()
                try:
                    flex_freq = next(coro)

                    self.add(time_schedule + flex_freq, coro, 0)
                except StopIteration:
                    print('Flexible coroutine completed')
            else:
                time.sleep(0.1)
        print("All coroutines completed")

class MixScheduler:
    def __init__(self):
        self._delayed = PriorityQueue()
        self._ready = []

    def add(self, coro, delay=0):
        if delay > 0:
            self._delayed.push((time.time() + delay, coro))
        else:
            self._ready.append(coro)

    def run(self):
        while self._delayed or self._ready:
            while self._delayed:
                time_schedule, coro = self._delayed.peek()
                if time.time() >= time_schedule:
                    self._delayed.pop()
                    self._ready.append(coro)
                else:
                    break
            if self._ready:
                for i in range(len(self._ready)):
                    coro = self._ready.pop(0)
                    try:
                        result = next(coro)
                        if isinstance(result, (int, float)) and result > 0:
                            self.add(coro, result)
                        else:
                            self._ready.append(coro)
                    except StopIteration:
                        continue
            else:
                time.sleep(0.1)

class Sleep:
    def __init__(self, seconds):
        self.seconds = seconds
    def __await__(self):
        yield self

class SleepScheduler(MixScheduler):
    def run(self):
        while self._delayed or self._ready:
            while self._delayed:
                time_schedule, coro = self._delayed.peek()
                if time.time() >= time_schedule:
                    self._delayed.pop()
                    self._ready.append(coro)
                else:
                    break
            if self._ready:
                for i in range(len(self._ready)):
                    coro = self._ready.pop(0)
                    try:
                        result = coro.send(None)
                        if isinstance(result, Sleep):
                            self.add(coro, result.seconds)
                        else:
                            self._ready.append(coro)
                    except StopIteration:
                        continue
            else:
                time.sleep(0.1)