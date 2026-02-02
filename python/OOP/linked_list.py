class Node:
    """ Node in singly linked list class implementation"""
    def __init__(self, data):
        """ Constructor for Node instance
        attributes: data, node next
        """
        self.data = data
        self.next = None

    def get_data(self):
        return self.data

    def set_data(self, data):
        self.data = data

    def set_next(self, next):
        """ Sets the next node to point at"""
        self.next = next

    def get_next(self):
        """ Returns the next node"""
        return self.next

class LinkedList:
    """ Singly linked list class implementation"""
    def __init__(self):
        """ Constructor for LinkedList"""
        self.len = 0
        self.head = None
        self.tail = None

    def __len__(self):
        """ Returns the number of nodes in the list"""
        return self.len

    def is_Empty(self):
        """ Returns True if list is empty,
        False otherwise
        """
        return self.len == 0

    def get_head_data(self):
        """ Returns the head data"""
        return self.head.get_data()

    def push(self, data):
        """ Push a new node with data
        to the end of the list
        """
        node = Node(data)
        if self.head is None:
            self.head = node
            self.tail = node
        else:
            self.tail.set_next(node)
            self.tail = node
        self.len += 1

    def pop(self):
        """ Pop the head element
        and returns its value
        """
        if self.is_Empty():
            return None
        tmp_node = self.head.get_next()
        data = self.head.get_data()
        self.head = tmp_node
        self.len -= 1
        if self.is_Empty():
            self.head = None
            self.tail = None
        return data

    def __str__(self):
        """ prints the list contents"""
        if self.is_Empty():
            return "Empty List"
        node = self.head
        ret_str = str(node.get_data())
        while node.get_next() is not None:
            node = node.get_next()
            ret_str += " " + str(node.get_data())
        return ret_str

