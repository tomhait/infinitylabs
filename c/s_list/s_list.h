#include <stddef.h>

typedef struct sll_t sll_t;
typedef struct node_t node_t;
typedef int (*for_each_func)(void*);
typedef int (*match_func)(void*, void*);

enum Status{
	FAIL,
	OK
};

/*
* Creates a singly linked list and return a pointer to it 
* Returns: sll_t* to the list (NULL if failed to create)
* O(1) time complexity
*/
sll_t* sll_create(void);

/*
* Appends a new node with "data" to the end of the list
* Returns: node_t* to the new appended node (NULL if failed) 
* O(1) time complexity
*/
node_t* sll_append(sll_t* lst, void* data); // returns NULL for failure

/*
* Inserts a new node with "data" after the "where" node in the list
* The function assumes that the "where" node exists in the list
* Returns: node_t* of the new inserted node (NULL if failed) 
* O(1) time complexity
*/
node_t* sll_insert(sll_t* lst, node_t* where, void* data);

/*
* Returns the data contained in node
* O(1) time complexity
*/
void* sll_get_data(node_t* node);

/*
* Replaces previous data in the node with the new provided data
* O(1) time complexity
*/
void sll_set_data(node_t* node, void* data);

/*
* Removes the last node in the list
* Returns the data of the removed node
* O(n) time complexity
*/
void* sll_pop(sll_t* lst);

/*
* Retuns the next node pointed by node
* O(1) time complexity
*/
node_t* sll_get_next(node_t* node);

/*
* Free the allocated nodes and the list
* O(n) time complexity
*/
void sll_destroy(sll_t* lst);

/*
* Retuns the number of nodes in the list
* O(1) time complexity
*/
size_t sll_get_count(const sll_t* lst);

/*
* Removes node from the list
* Returns OK status if succeeded (FAIL if not)
* O(1) time complexity
*/
int sll_remove(sll_t* lst, node_t* node);

/*
* Applies func on each node in the list
* Returns OK status if succeeded (FAIL if not)
* O(n) time complexity
*/
int sll_for_each(sll_t* lst, for_each_func func);

/*
* Applies the match func on each node in the list and compare it with param
* Returns node_t* to the node that its data matched to the param (NULL if not found)
* O(n) time complexity
*/
node_t* sll_find(sll_t* list, void* param, match_func func);


