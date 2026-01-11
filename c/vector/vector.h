#include <stddef.h>


typedef struct vector_t vector_t;

vector_t* vec_create(const size_t capacity);                             /* creates a vector starting with x elements (by default x should perhaps be 1) */
void* vec_get_element(const vector_t* vec, const size_t idx);            /* return a void pointer to element located at position idx of our void vector */
void vec_push(vector_t* vec, void* new_element);               /* add a new element to the end of void vector */
void* vec_pop(vector_t* vec);                                        /* remove last element from end of void vector & return value it holds (also void pointer) */
void vec_set_element(vector_t* vec, const size_t idx, void* element);    /* -- purpose? -- */ 
size_t vec_get_size(const vector_t* vec);                                /* get size of void vector -- should probably be *update* size not *get* size */
size_t vec_get_capacity(const vector_t* vec);                            /* get potential capacity of void vector -- again, should be *update* not *get* */
void vec_destroy(vector_t* vec);                                         /* free the entire void vector and what is is pointing at from memory */
