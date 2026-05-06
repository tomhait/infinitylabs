from bst import BST

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

if __name__ == "__main__":
    test1()
    test2()
    test3()