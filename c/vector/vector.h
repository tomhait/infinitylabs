#include <stddef.h>


typedef struct vector_t vector_t;

/* 
*  creates a vector starting with "capacity" elements
*  Returns: 
*  Pointer to vector_t
*  NULL if couldn't create a vector 
*/
vector_t* vec_create(const size_t capacity);                             

/* 
* Returns a void pointer to element located at position idx of our void vector
* Returns NULL if idx is larger than the number of occupied slots
* O(1) time complexity
*/
void* vec_get_element(const vector_t* vec, const size_t idx);            

/* 
* add a new element to the end of void vector
* Returns nothing if couldn't extend the vector 
* O(1) Amortized time complexity (O(n) for resizing, O(1) for push without resizing)
*/
void vec_push(vector_t* vec, void* new_element);

/* 
* remove last element from end of void vector & return value it holds (also void pointer)
* Returns a pointer to the popped element 
* O(1) time complexity
*/
void* vec_pop(vector_t* vec);

/* 
* Switch the element at index idx with a new element
* Returns nothing if idx > vector occupied size 
* O(1) time complexity
*/
void vec_set_element(vector_t* vec, const size_t idx, void* element); 

/* 
* Get the occupied size of the vector 
* O(1) time complexity
*/
size_t vec_get_size(const vector_t* vec);

/* 
* Get the full size of the vector (including not occupied positions) 
* O(1) time complexity
*/
size_t vec_get_capacity(const vector_t* vec);

/* 
* Free the allocated memeory for the dynamic vector and the struct vector_t itself 
* O(1) time complexity
*/
void vec_destroy(vector_t* vec);

