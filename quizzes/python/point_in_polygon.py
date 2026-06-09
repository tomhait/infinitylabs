class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return f"Point({self.x},{self.y})"

def is_inside(p: Point, polygon: list):
    x_vals = [p1.x for p1 in polygon]
    y_vals = [p1.y for p1 in polygon]

    min_x = min(x_vals)
    max_x = max(x_vals)
    min_y = min(y_vals)
    max_y = max(y_vals)

    inside = True
    if p.x <= min_x or p.x >= max_x:
        inside = False
    if p.y <= min_y or p.y >= max_y:
        inside = False
    return inside

## using ray casting algorithm
def point_in_polygon(p, polygon):
    x, y = p.x, p.y
    inside = False
    n = len(polygon)

    j = n - 1
    for i in range(n):
        xi, yi = polygon[i].x, polygon[i].y
        xj, yj = polygon[j].x, polygon[j].y

        intersects = ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / (yj - yi) + xi
        )

        if intersects:
            inside = not inside

        j = i

    return inside

polygon = [Point(0,0),Point(0,3),
           Point(3,0),Point(3,3)]

p = Point(2,2)

print(p, "is inside: ", is_inside(p, polygon))
print(p, "is inside: ", point_in_polygon(p, polygon))

p = Point(1,3)

print(p, "is inside: ", is_inside(p, polygon))
print(p, "is inside: ", point_in_polygon(p, polygon))

polygon = [Point(0,0),Point(0,3), Point(1,1),
           Point(3,3),Point(3,0)]

p = Point(0.5,0.5)

print(p, "is inside: ", is_inside(p, polygon))
print(p, "is inside: ", point_in_polygon(p, polygon))

p = Point(1,1.5)

print(p, "is inside: ", is_inside(p, polygon))
print(p, "is inside: ", point_in_polygon(p, polygon))
