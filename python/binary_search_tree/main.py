from bst import BST
from bstAVL import BSTAVL
def test1():
    print("\n--------------\nTest 1\n--------------")
    lst = [25, 15, 10, 4, 12, 22, 18, 24, 50, 31, 35, 44, 70, 66, 90]
    bst = BST()
    for val in lst:
        bst.insert(val)
    print("Test: BST Size")
    assert len(bst) == 15
    print("Passed")
    # in order
    output = []
    for i in bst:
        output.append(i)
    print("Test: In-order")
    print(", ".join([str(i) for i in output]))
    assert output == sorted(lst)
    print("Passed")
    output = []
    for i in bst.pre_order():
        output.append(i)
    print("Test: Pre-order")
    print(", ".join([str(i) for i in output]))
    assert output == [25, 15, 10, 4, 12, 22, 18, 24, 50, 31, 35, 44, 70, 66, 90]
    print("Passed")
    output = []
    for i in bst.post_order():
        output.append(i)
    print("Test: Post-order test")
    print(", ".join([str(i) for i in output]))
    assert output == [4, 12, 10, 18, 24, 22, 15, 44, 35, 31, 66, 90, 70, 50, 25]
    print("Passed")
    print("--------------\nPassed Test 1\n--------------")

def test2():
    print("\n--------------\nTest 2\n--------------")
    lst = ['a','1','3','4','ab']
    bst = BST()
    for val in lst:
        bst.insert(val)
    print("Test: BST Size")
    assert len(bst) == 5
    print("Passed")
    output = []
    for i in bst:
        output.append(i)
    print("Test: In-order")
    print(", ".join([str(i) for i in output]))
    assert output == sorted(lst)
    print("Passed")
    print("Test: item in BST")
    assert ('a' in bst) == True
    assert ('b' in bst) == False
    print("Passed")
    print('Test: remove item from BST')
    bst.remove('ab')
    assert ('ab' in bst) == False
    print("Passed")
    output = []
    for i in bst:
        output.append(i)
    print("Test: In-order")
    print(", ".join([str(i) for i in output]))
    assert output == sorted(output)
    print("Passed")
    print("--------------\nPassed Test 2\n--------------")

def test3():
    print("\n--------------\nTest 3\n--------------")
    lst = ['a', '1']
    bst = BST()
    for val in lst:
        bst.insert(val)
    print("Test: BST Size")
    assert len(bst) == 2
    print("Passed")
    print("Test: In-order")
    output = []
    for i in bst:
        output.append(i)
    print(", ".join([str(i) for i in output]))
    assert output == sorted(lst)
    print("Passed")
    print('Test: remove item from BST')
    bst.remove('a')
    bst.remove('1')
    assert len(bst) == 0
    print("Passed")
    lst = [3,1,4,0]
    for val in lst:
        bst.insert(val)
    print("Test: BST Size")
    assert len(bst) == 4
    print("Passed")
    print("Test: In-order")
    output = []
    for i in bst:
        output.append(i)
    print(", ".join([str(i) for i in output]))
    assert output == sorted(lst)
    print("Passed")
    print("--------------\nPassed Test 3\n--------------")


def remove_test(ordered_list, item_to_remove, output_pre_test, output_post_test):
    bst = BST()
    for val in ordered_list:
        bst.insert(val)
    bst.remove(item_to_remove)

    output_pre = []
    output_post = []
    for i in bst.pre_order():
        output_pre.append(i)

    for i in bst.post_order():
        output_post.append(i)

    assert output_pre == output_pre_test
    assert output_post == output_post_test
    print("passed")


def test4():
    print("---- delete root test ----")

    print(" root has no childs ")
    items = [1]
    delete_order = [1]
    output_pre = []
    output_post = []
    remove_test(items, delete_order[0], output_pre, output_post)

    print(" root has one right child ")
    items = [1, 2]
    delete_order = [1]
    output_pre = [2]
    output_post = [2]
    remove_test(items, delete_order[0], output_pre, output_post)

    print(" root has one right child and the child has right child")
    items = [1, 2, 3]
    delete_order = [1]
    output_pre = [2, 3]
    output_post = [3, 2]
    remove_test(items, delete_order[0], output_pre, output_post)

    print(" root has one right child and the child has left child")
    items = [1, 3, 2]
    delete_order = [1]
    output_pre = [3, 2]
    output_post = [2, 3]
    remove_test(items, delete_order[0], output_pre, output_post)

    print(" root has one right child and the child has left child and he has right child")
    items = [1, 4, 2, 3]
    delete_order = [1]
    output_pre = [4, 2, 3]
    output_post = [3, 2, 4]
    remove_test(items, delete_order[0], output_pre, output_post)

    print(" root has one left child ")
    items = [3, 2]
    delete_order = [3]
    output_pre = [2]
    output_post = [2]
    remove_test(items, delete_order[0], output_pre, output_post)

    print(" root has 2 childs ")
    items = [2, 1, 3]
    delete_order = [2]
    output_pre = [3, 1]
    output_post = [1, 3]
    remove_test(items, delete_order[0], output_pre, output_post)

    print(" root has 2 childs and the right child has left child")
    items = [2, 1, 5, 3]
    delete_order = [2]
    output_pre = [3, 1, 5]
    output_post = [1, 5, 3]
    remove_test(items, delete_order[0], output_pre, output_post)

    print(" root has 2 childs and the right child has left child and he has right child")
    items = [2, 1, 5, 3, 4]
    delete_order = [2]
    output_pre = [3, 1, 5, 4]
    output_post = [1, 4, 5, 3]
    remove_test(items, delete_order[0], output_pre, output_post)

    print("----delete not-root node----")
    print(" node is a right and has no childs ")
    items = [-10, 1]
    delete_order = [1]
    output_pre = [-10]
    output_post = [-10]
    remove_test(items, delete_order[0], output_pre, output_post)

    print(" node is a right and  has one right child ")
    items = [-10, 1, 2]
    delete_order = [1]
    output_pre = [-10, 2]
    output_post = [2, -10]
    remove_test(items, delete_order[0], output_pre, output_post)

    print(" node is a right and  has one right child and the child has right child")
    items = [-10, 1, 2, 3]
    delete_order = [1]
    output_pre = [-10, 2, 3]
    output_post = [3, 2, -10]
    remove_test(items, delete_order[0], output_pre, output_post)

    print(" node is a right and  has 2 cilds, the right child and the child has left child")
    items = [-10, 1, 0, 3, 2]
    delete_order = [1]
    output_pre = [-10, 2, 0, 3]
    output_post = [0, 3, 2, -10]
    remove_test(items, delete_order[0], output_pre, output_post)

    print(
        " node is a right and  has 2 childs, the right child has left child and he has right child")
    items = [-10, 1, 0, 4, 2, 3]
    delete_order = [1]
    output_pre = [-10, 2, 0, 4, 3]
    output_post = [0, 3, 4, 2, -10]
    remove_test(items, delete_order[0], output_pre, output_post)

    print(" node is a right and  has one left child ")
    items = [-10, 3, 2]
    delete_order = [3]
    output_pre = [-10, 2]
    output_post = [2, -10]
    remove_test(items, delete_order[0], output_pre, output_post)

    print(" node is a right and  has 2 childs ")
    items = [-10, 2, 1, 3]
    delete_order = [2]
    output_pre = [-10, 3, 1]
    output_post = [1, 3, -10]
    remove_test(items, delete_order[0], output_pre, output_post)

    print(" node is a right and  has 2 childs and the right child has left child")
    items = [-10, 2, 1, 5, 3]
    delete_order = [2]
    output_pre = [-10, 3, 1, 5]
    output_post = [1, 5, 3, -10]
    remove_test(items, delete_order[0], output_pre, output_post)
    print(
        " node is a right and  has 2 childs and the right child has left child and he has right child")
    items = [-10, 2, 1, 5, 3, 4]
    delete_order = [2]
    output_pre = [-10, 3, 1, 5, 4]
    output_post = [1, 4, 5, 3, -10]
    remove_test(items, delete_order[0], output_pre, output_post)


if __name__ == "__main__":
    test1()
    test2()
    test3()
    test4()