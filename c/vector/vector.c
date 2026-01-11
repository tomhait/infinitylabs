#include "vector.h"
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>

#define GROWTH_FACTOR 2
#define EMPTY -1
	
struct vector_t{
	size_t occupied_size;
	size_t capacity;
	void **vals;
};


vector_t* vec_create(const size_t capacity){
	vector_t *vec = (vector_t*)malloc(sizeof(vector_t));
	if(vec == NULL){
		perror("Memory alloacation failed");
		return NULL;
	}	
	vec->occupied_size = 0;
	vec->capacity=capacity;
	vec->vals = (void**)malloc(vec->capacity*sizeof(void*));
	if(vec->vals == NULL){
		perror("Memory alloacation failed");
		free(vec);
		return NULL;
	}
	return vec;
}

void* vec_get_element(const vector_t* vec, const size_t idx){
	if(vec->capacity < idx){
		printf("Out of capacity\n");
		return NULL;
	}
	return vec->vals[idx];
}

static int ExtendVector(vector_t *vec){
	vec->vals = realloc(vec->vals, vec->capacity*GROWTH_FACTOR*sizeof(void*));
	if(vec->vals == NULL){
		perror("Memory alloacation failed");
		return EMPTY;
	}
	vec->capacity = vec->capacity*GROWTH_FACTOR;
	return 0;	
}

void vec_push(vector_t* vec, void* new_element){
	if(vec->occupied_size == vec->capacity){
		if(ExtendVector(vec)==EMPTY){
			return;
		}
	}
	vec->vals[vec->occupied_size] = new_element;
	vec->occupied_size++;
}


void* vec_pop(vector_t* vec){
	if(vec->occupied_size==0){
		printf("Nothing to pop\n");
		return NULL;
	}
	void* ret_val = vec_get_element(vec, vec->occupied_size-1);
	vec->vals[vec->occupied_size-1] = NULL;
	vec->occupied_size--;
	return ret_val;
}

void vec_set_element(vector_t* vec, const size_t idx, void* element){
	if(idx > vec->occupied_size){
		printf("Cannot set unoccupied position, Vector is continuous\n");
		return;  
	}
	vec->vals[idx] = element;
}

size_t vec_get_size(const vector_t* vec){
	return vec->occupied_size;
}
size_t vec_get_capacity(const vector_t* vec){
	return vec->capacity;
}

void vec_destroy(vector_t* vec){
	free(vec->vals);
	free(vec);
}

