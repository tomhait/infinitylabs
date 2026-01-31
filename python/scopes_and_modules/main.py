from modules import *
from areas import *

if __name__ == '__main__':
    r = 2
    w = 10
    h = 5

    print(f"Circle area for r={r}: {circle_area(r):.2f}")
    print(f"Triangle area for w={w} and h={h}: {triangle_area(w, h):.2f}")
    print(f"Rectangle area for w={w} and h={h}: {rectangle_area(w, h):.2f}")

    print_os_info()

    reverse_args()

change_file_permissions("test_permissions.txt")
print(stat.filemode(os.stat("test_permissions.txt").st_mode))