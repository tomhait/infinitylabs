from __future__ import annotations
from dataclasses import dataclass
from typing import Iterator, Any

@dataclass
class Node:
    '''
    Defines a basic node with a value, and left (smaller) and right (larger) children.
    '''
    value: Any
    value_num: int = -1
    left: Node | None = None
    right: Node | None = None

class BST:
    '''
        Define the basic binary search tree with root node.
    '''

    def __init__(self):
        self.root: Node | None = None

    def _compare(self, a: Any, b: Any):
        if a == b: return 0
        return -1 if a < b else 1

    def _create_node(self, value):
        node = Node(value)
        if isinstance(value, str):
            node.value_num = sum(map(ord, value))
        else:
            node.value_num = value
        return node

    def insert(self, value: Any) -> None:
        '''
        Gets a value of int, float or a char, creates a new node with that value in the tree.
        Raises ValueError if the value already exists in a different node.
        Raises TypeError if the value isn't comparable to all the basic types.
        '''
        if not isinstance(value,(int,float,str)):
            raise TypeError('The value is not comparable')
        if value in self:
            raise ValueError('The value is already inside the tree')
        node = self._create_node(value)
        if self.root is None:
            self.root = node
        else:
            self._insert_rec(self.root, node)

    def _insert_rec(self, current, node):
        comp = self._compare(current.value_num, node.value_num)
        if comp > 0:
            if current.left is None:
                current.left = node
            else:
                self._insert_rec(current.left, node)
        else:
            if current.right is None:
                current.right = node
            else:
                self._insert_rec(current.right, node)

    def is_empty(self) -> bool:
        '''
        True if tree length is 0, false otherwise.
        '''
        return len(self) == 0

    def remove(self, value: Any) -> None:
        '''
        Gets a value, and removes the node with that value from the tree.
        removes the node, if it has any children, it will be replaced by the smallest node on the right and the tree will be reorderd
        Raises valueError if there isn't a node with that value.

        '''
        if value not in self:
            raise ValueError(f'There isn\'t a node value: {value}')

        target_node_data = self._create_node(value)
        self.root = self._remove_rec(self.root, target_node_data)

    def _remove_rec(self, current: Node | None, target: Node):
        if current is None:
            return None
        comp = self._compare(current.value_num, target.value_num)
        if comp > 0:
            current.left = self._remove_rec(current.left, target)
        elif comp > 0:
            current.right = self._remove_rec(current.right, target)
        else:
            if current.left is None:
                return current.right
            if current.right is None:
                return current.left
            successor = self._get_min_rec(current.right)
            current.value = successor.value
            current.value_num = successor.value_num
            current.right = self._remove_rec(current.right, successor)
        return current

    def _contains_rec(self, current: Node, node: Node):
        if current is None:
            return False
        comp = self._compare(current.value_num, node.value_num)
        if comp == 0:
            return True
        if comp > 0:
            return self._contains_rec(current.left, node)
        return self._contains_rec(current.right, node)

    def __contains__(self, value: Any) -> bool:
        '''
        Returns True if the value exists, False otherwise
        '''
        node = self._create_node(value)
        return self._contains_rec(self.root, node)

    def _pre_order_rec(self, node):
        if node is not None:
            yield node.value
            yield from self._pre_order_rec(node.left)
            yield from self._pre_order_rec(node.right)

    def pre_order(self) -> Iterator[Any]:
        '''
        returns a pre-order iterator
        '''
        yield from self._pre_order_rec(self.root)

    def _inorder_rec(self, node):
        if node is not None:
            yield from self._inorder_rec(node.left)
            yield node.value
            yield from self._inorder_rec(node.right)

    def in_order(self) -> Iterator[Any]:
        '''
        returns an in-order iterator
        '''
        yield from self._inorder_rec(self.root)

    def _post_order_rec(self, node):
        if node is not None:
            yield from self._post_order_rec(node.left)
            yield from self._post_order_rec(node.right)
            yield node.value

    def post_order(self) -> Iterator[Any]:
        '''
        returns a post-order iterator
        '''
        yield from self._post_order_rec(self.root)

    def __len__(self) -> int:
        '''
        Number of nodes
        '''
        return len(list(self.in_order()))

    def __iter__(self) -> Iterator[Any]:
        '''
        In-order iterator
        '''
        return self.in_order()

