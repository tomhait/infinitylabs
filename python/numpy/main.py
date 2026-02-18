from functions import *
from PIL import Image
import matplotlib.pyplot as plt

def do_1():
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

def do_2():
    print(get_random_mat((3, 3)))

def do_3():
    with Image.open("./Lenna.png") as img:
        img_array = np.array(img)[:,:,0]
        img_array = get_central_part(img_array)
        print(img_array.shape)
        print(img_array.dtype)
        plt.imshow(img_array, cmap='gray')
        plt.axis('off')
        plt.show()

def do_4():
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

def do_5():
    x, y = create_quadratic_ds()
    print(y)
    print(np.mean(y))
    print(np.std(y))

def do_6():
    x, y = create_quadratic_ds(500000)
    y_pred = apply_ols_quad(x, y)
    plt.scatter(x, y, label='Data', alpha=0.5)
    plt.plot(x, y_pred, color='red', label='Quadratic Fit')
    plt.xlabel('x')
    plt.ylabel('y')
    plt.title('Quadratic Regression with numpy.polyfit')
    plt.legend()
    plt.show()

def do_7():
    mat1 = get_random_mat((2, 3))
    mat2 = get_random_mat((2, 3))
    vec1 = get_random_mat((3, 1))
    print(mat1)
    print(mat2)
    print(mat1.T)
    print(mat1 @ mat2.T)
    print(np.dot(mat1[0,:], mat2[0,:]))
    print(np.linalg.norm(mat1[0,:]))
    # normalizing a vector to its unit length
    print(np.linalg.norm(mat1[0,:] / np.linalg.norm(mat1[0,:])))
    probs = softmax(mat1[0, :])
    print(probs)
    print("Sum of probabilities:", np.sum(probs))
    print(np.argmax(np.abs(mat1)))
    print(np.argmax(np.abs(mat2)))


if __name__ == "__main__":
    # do_1()
    # do_2()
    # do_3()
    # do_4()
    # do_5()
    # do_6()
    do_7()


