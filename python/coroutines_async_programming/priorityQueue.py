import heapq

class PriorityQueue:
    def __init__(self):
        self._queue = []

    def push(self, item):
        """
        Adds an item to the queue.
        Expects item to be comparable.
        """
        heapq.heappush(self._queue, item)

    def pop(self):
        """Removes and returns the highest priority (smallest value) item."""
        if self.is_empty():
            print("Queue is already empty")
            return None
        return heapq.heappop(self._queue)

    def peek(self):
        if self.is_empty():
            return None
        return self._queue[0]

    def is_empty(self):
        return len(self._queue) == 0

    def __len__(self):
        return len(self._queue)