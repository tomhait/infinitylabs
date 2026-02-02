from point import *
from linked_list import LinkedList

if __name__ == "__main__":
    # p = Point()
    # print(p)
    # p = Point(1,"tom")
    # print(p)
    # p = Point(2,2)
    # print(p)
    # print(f"Point distance from origin: {p.distance():.2f}")
    lst = LinkedList()
    lst.push(1)
    lst.push(2)
    lst.push(3)
    print(lst)
    print(len(lst))
    print(lst.pop())
    print(len(lst))
    print(lst.get_head_data())
    lst.pop()
    lst.pop()
    print(lst)
    lst.push(4)
    print(lst)
    print(lst.get_head_data())


