import time
from point import *
from linked_list import LinkedList
from Machine import *

if __name__ == "__main__":
    # Exercise 1
    p = Point()
    print(p)
    p = Point(1,"tom")
    print(p)
    p = Point(2,2)
    print(p)
    print(f"Point distance from origin: {p.distance():.2f}")

    # Exercise 2
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

    ## Exercise 3
    cloud = Cloud()
    a = MachineType1()
    b = MachineType1()
    c = MachineType1()
    d = MachineType2()
    cloud.add_machine(a)
    cloud.add_machine(b)
    cloud.add_machine(c)
    cloud.add_machine(d)
    for mach in cloud.machines:
        mach.start_machine()
    print(len(cloud))
    time.sleep(60)
    print(a)
    print(d)
    e = MachineType2()
    e.start_machine()
    cloud.add_machine(e)
    print(len(cloud))
    time.sleep(60)
    print(a)
    print(d)
    b.stop_machine()
    time.sleep(60)
    print(a)
    print(b)
    print(c)
    print(d)
    print(e)
    print(f"The total cost of running the machines is: {cloud.get_tot_price():.2f}")


