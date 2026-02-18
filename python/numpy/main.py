from functions import *
from PIL import Image
import matplotlib.pyplot as plt

def do_test_1():
    n=10000000
    a_list = zero_list(n)
    a_np = zero_np(n)

    a_list1 = add_const(a_list, val = 1)
    a_list2 = add_const(a_list)
    a_np1 = add_const(a_np, val = 1)
    a_np2 = add_const(a_np)

    dot_prod(a_list1, a_list2)
    dot_prod(a_np1, a_np2)

    apply_exp(a_list1)
    apply_exp(a_np1)

    concat(a_list1, a_list2)
    concat(a_np1, a_np2)

    print_elem(a_list1)
    print_elem(a_np1)

def do_test_2():
    print(get_random_mat((3, 3)))

def do_test_3():
    with Image.open("./Lenna.png") as img:
        img_array = np.array(img)[:,:,0]
        img_array = get_central_part(img_array)
        print(img_array.shape)
        print(img_array.dtype)
        plt.imshow(img_array, cmap='gray')
        plt.axis('off')
        plt.show()

def do_test_4():
    mat1 = np.genfromtxt("./data.csv", delimiter=',')
    mat2 = np.genfromtxt("./incomplete_data.csv", delimiter=',')
    mat1_stand = standard_matrix(mat1)
    print(np.nanmean(mat1,axis=0))
    print(np.nanstd(mat1, axis=0))
    print(np.nanmean(mat1_stand,axis=0))
    print(np.nanstd(mat1_stand, axis=0))
    mat2_stand = standard_matrix(mat2)
    print(np.nanmean(mat2_stand,axis=0))
    print(np.nanstd(mat2_stand, axis=0))
    mat1_stand = standard_matrix(mat1, axis=1)
    print(np.nanmean(mat1_stand,axis=1))
    print(np.nanstd(mat1_stand, axis=1))
    mat2_stand = standard_matrix(mat2, axis=1)
    print(np.nanmean(mat2_stand,axis=1))
    print(np.nanstd(mat2_stand, axis=1))

if __name__ == "__main__":
    # do_test_1()
    # do_test_2()
    # do_test_3()
    do_test_4()


