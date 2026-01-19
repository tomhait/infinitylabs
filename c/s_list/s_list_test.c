#include "s_list.h"
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>

#define UNUSED(x) (void)(x)

int Increment(void* data, void* params){
	UNUSED(params);
	(*(int*)data)++;
	return 0;
}

int printData(void* data, void* params){
	UNUSED(params);
	printf("%d\n", *(int*)data);
	return 0;
}

int IsEqual(void* d1, void* d2){
	return *((int*)d1) == *((int*)d2);
}

int main(){
	int arr[] = {1,2};
	size_t size = sizeof(arr)/sizeof(arr[0]);
	int dataForInsert = 56;
	node_t** nodes = (node_t**)malloc(size*sizeof(node_t*));
	if(!nodes) return -1;
	sll_t* list = sll_create();
	for(size_t i=0; i < size; i++){
		nodes[i] = sll_append(list, &arr[i]);
	}
	assert(sll_get_count(list)==size);
	sll_for_each(list, printData, NULL);
	sll_for_each(list, Increment, NULL);
	printf("\n\n\n");
	sll_for_each(list, printData, NULL);
	printf("\n\n\n");
	node_t* where = nodes[0];
	node_t* insertedNode = sll_insert(list, where, &dataForInsert);
	assert(*((int*)sll_get_data(insertedNode)) == dataForInsert);
	sll_for_each(list, printData, NULL);
	printf("\n\n\n");
	sll_set_data(nodes[0], &dataForInsert);
	sll_for_each(list, printData, NULL);
	printf("\n\n\n");
	node_t* next = sll_get_next(nodes[0]);
	assert(next==nodes[1]);
	assert(*((int*)sll_pop(list))==56);
	assert(sll_get_count(list)==size);
	sll_for_each(list, printData, NULL);
	printf("\n\n\n");

	sll_remove(list, nodes[0]);
	sll_for_each(list, printData, NULL);
	printf("\n\n\n");
	assert(sll_get_count(list)==1);
	node_t *nd = sll_find(list, &dataForInsert, IsEqual);
	if(nd!=NULL) assert(*((int*)sll_get_data(nd))==dataForInsert);	
	sll_destroy(list);
	free(nodes);
	
	//Testing a list of one element - boundary value
	int arr2[] = {1};
	sll_t* list2 = sll_create();
	sll_append(list2, &arr2[0]);
	assert(*((int*)sll_pop(list2))==1);
	assert(sll_get_count(list2)==0);
	sll_append(list2, &arr2[0]);
	assert(*((int*)sll_pop(list2))==1);
	sll_destroy(list2);
	
	return 0;
}
