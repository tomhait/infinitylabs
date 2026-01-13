#include "s_list.h"
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>

void Increment(int* data){
	*data++;
}

int IsEqual(int* d1, int* d2){
	return *d1 == *d2;
}

int main(){
	int arr[] = {1,2,7,4,5,6,7,8};
	size_t size = sizeof(arr)/sizeof(arr[0]);
	int dataForInsert = 56;
	node_t** nodes = (node_t**)malloc(size*sizeof(node_t*));
	if(!nodes) return -1;
	sll_t* list = sll_create();
	for(size_t i=0; i < size; i++){
		nodes[i] = sll_append(list, &arr[i]);
	}
	assert(sll_get_count(list)==size);
	node_t* where = nodes[4];
	node_t* insertedNode = sll_insert(list, where, &dataForInsert);
	assert(*((int*)sll_get_data(insertedNode)) == dataForInsert);
	sll_destroy(list);
	free(nodes);
	return 0;
}
