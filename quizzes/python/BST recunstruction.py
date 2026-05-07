def bst_reconstruct(inorder: str, levorder: str):
    if len(levorder) == 0:
        return
    if len(inorder) == 0:
        return
    root = levorder[0]
    pos = inorder.index(root)
    left_in = inorder[:pos]
    right_in = inorder[pos+1:]
    left_lev = "".join([c for c in levorder if c in left_in])
    right_lev = "".join([c for c in levorder if c in right_in])
    left_res = bst_reconstruct(left_in, left_lev)
    right_res = bst_reconstruct(right_in, right_lev)

    if not left_res and not right_res:
        return root

    return f"{root}:({left_res},{right_res})"

print(bst_reconstruct("khfsrotcae", "ersofchtak"))