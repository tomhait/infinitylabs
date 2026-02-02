from point import *

if __name__ == "__main__":
    p = Point()
    print(p)
    p = Point(1,"tom")
    print(p)
    p = Point(2,2)
    print(p)
    print(f"Point distance from origin: {p.distance():.2f}")

