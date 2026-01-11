#include <stdio.h>
#include "vector.h"

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
	printf("Vector size and occupation are: %ld %ld\n", vec_get_capacity(vec), vec_get_size(vec));
	printf("Popped the variable: %s\n",(char*)vec_pop(vec));
	printf("Vector size and occupation are: %ld %ld\n", vec_get_capacity(vec), vec_get_size(vec));
	vec_set_element(vec, 0, s2);
	printf("Element at 0 position is: %s\n",(char*)vec_get_element(vec, 0));
	printf("Element at 1 position is: %d\n",*((int*)vec_get_element(vec, 1)));
	vec_destroy(vec);
	return 0;
}
