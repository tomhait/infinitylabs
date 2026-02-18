from functions import *
from PIL import Image
import matplotlib.pyplot as plt

if __name__ == "__main__":
    # n=10000000
    # a_list = zero_list(n)
    # a_np = zero_np(n)
    #
    # a_list1 = add_const(a_list, val = 1)
    # a_list2 = add_const(a_list)
    # a_np1 = add_const(a_np, val = 1)
    # a_np2 = add_const(a_np)
    #
    # dot_prod(a_list1, a_list2)
    # dot_prod(a_np1, a_np2)
    #
    # apply_exp(a_list1)
    # apply_exp(a_np1)
    #
    # concat(a_list1, a_list2)
    # concat(a_np1, a_np2)
    #
    # print_elem(a_list1)
    # print_elem(a_np1)

    print(get_random_mat((3,3)))
    with Image.open("./Lenna.png") as img:
        img_array = np.array(img)[:,:,0]
        img_array = get_central_part(img_array)
        print(img_array.shape)
        print(img_array.dtype)
        plt.imshow(img_array, cmap='gray')
        plt.axis('off')
        plt.show()

