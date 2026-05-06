from bst import BST

def test1():
    lst = [25, 15, 10, 4, 12, 22, 18, 24, 50, 31, 35, 44, 70, 66, 90]
    bst = BST()
    for val in lst:
        bst.insert(val)
    print("\n",len(bst) == 15)
    # in order
    output = []
    for i in bst:
        output.append(i)
    print("\n")
    print("In-order")
    print(", ".join([str(i) for i in output]))

    output = []
    for i in bst.pre_order():
        output.append(i)
    print("\n")
    print("Pre-order")
    print(", ".join([str(i) for i in output]))

    output = []
    for i in bst.post_order():
        output.append(i)
    print("\n")
    print("Post-order")
    print(", ".join([str(i) for i in output]))

def test2():
    lst = ['a',1,3,4,'ab']
    bst = BST()
    for val in lst:
        bst.insert(val)
    print(len(bst))
    # in order
    output = []
    for i in bst:
        output.append(i)
    print("\n")
    print("In-order")
    print(", ".join([str(i) for i in output]))
    print('a' in bst)
    print('b' in bst)
    bst.remove('ab')
    print('ab' in bst)
    output = []
    for i in bst:
        output.append(i)
    print("\n")
    print("In-order")
    print(", ".join([str(i) for i in output]))

if __name__ == "__main__":
    test1()
    test2()
