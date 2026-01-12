#include <stdio.h>
#include "vector.h"
#include <string.h>
#include <assert.h>

int main(){
	vector_t *vec = vec_create(2);
	int x1 = 1, x2 = 2, x3 = 3;
	char *s1 = "Hello";
	char *s2 = "World!";
	vec_push(vec, &x1);
	vec_push(vec, &x2);
	vec_push(vec, &x3);
	vec_push(vec, s1);
	vec_push(vec, s2);
	assert(vec_get_capacity(vec)==8);
	assert(vec_get_size(vec)==5);
	assert(strcmp(s2,(char*)vec_pop(vec))==0);
	assert(vec_get_capacity(vec)==8);
	assert(vec_get_size(vec)==4);	
	vec_set_element(vec, 0, s2);
	assert(strcmp(s2,(char*)vec_get_element(vec, 0))==0);
	assert(*((int*)vec_get_element(vec, 1))==x2);
	vec_destroy(vec);
	return 0;
}
