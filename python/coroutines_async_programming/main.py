import pytest
from priorityQueue import PriorityQueue

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




