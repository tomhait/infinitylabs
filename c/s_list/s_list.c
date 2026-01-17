#include "s_list.h"
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>

struct sll_t{
	size_t count;
	node_t* dummy;
	node_t* head;
	node_t* tail;
};

struct node_t{
	void* data;
	node_t* next;
};

static node_t* CreateNode(void* data){
	node_t* node = (node_t*)malloc(sizeof(node_t));
	if(!node) return NULL;
	node->data = data;
	node->next = NULL;
	return node;
}

sll_t* sll_create(void){
	sll_t* list = (sll_t*)malloc(sizeof(sll_t));
	if(!list) return NULL;
	node_t *dummy = CreateNode(NULL);
	if(!dummy){
		free(list);
		return NULL;
	}
	list->dummy = dummy;
	list->head = NULL;
	list->tail = NULL;
	list->count = 0;
	return list;
}

node_t* sll_append(sll_t* list, void* data){
	node_t* node = CreateNode(data);
	if(!node) return NULL;
	if(!list->head){
		list->head = node;
		list->tail = node;
	} else {
		list->tail->next = node;
		list->tail = node;
	}
	list->tail->next = list->dummy;
	list->count++;
	return node;
}

node_t* sll_insert(sll_t* list, node_t* where, void* data){
	node_t* node = CreateNode(data);
	if(!node) return NULL;
	if(where == list->head){
		node->next = list->head;
		list->head = node;
	}else{
		node->next = where->next;
		where->next = node;
		if(where == list->tail){
			list->tail = node;
			list->tail->next = list->dummy;
		}
	}
	/*if(list->tail == where){
		list->tail = node;
		list->tail->next = list->dummy;
	}*/
	list->count++;
	return node;
}

void* sll_get_data(node_t* node){
	return node->data;
}

void sll_set_data(node_t* node, void* data){
	node->data = data;
}

void* sll_pop(sll_t* list){
	void* outData = list->head->data;
	node_t *tmp = list->head;
	list->head = list->head->next;
	list->count--;
	if(list->count==0){
		list->head = NULL;
		list->tail = NULL;
	}
	free(tmp);
	tmp = NULL;
	return outData;
}

node_t* sll_get_next(node_t* node){
	if(!node) return NULL;
	return node->next;
}

void sll_destroy(sll_t* list){
	while(list->count != 0){
		node_t* tmp = list->head;
		list->head = list->head->next;
		free(tmp);
		list->count--;
	}
	free(list->dummy);
	free(list);
}

size_t sll_get_count(const sll_t* list){
	return list->count;
}

int sll_remove(sll_t* list, node_t* node){
	if(list->count==0) return FAIL;
	node_t* tmp = node->next;
	node->data = tmp->data;
	node->next = tmp->next;
	if(node == list->tail){
		list->dummy = node;
	}
	if(tmp!=list->dummy){
		free(tmp);
		tmp = NULL;
		list->count--;
	}
	if(list->count==0){
		list->head = NULL;
		list->tail = NULL;
	}
	return OK;
}

int sll_for_each(sll_t* list, for_each_func func){
	node_t *current = list->head;
	while(current != list->dummy){
		func(current->data);
		current = current->next;
	}
	return OK;
}

node_t* sll_find(sll_t* list, void* param, match_func func){
	node_t *current = list->head;
	while(current != list->dummy){
		if(func(current->data, param)){
			return current;
		}
		current = current->next;
	}
	return NULL;
}

node_t* sll_get_head(sll_t* list){
	return list->head;
}

node_t* sll_get_tail(sll_t* list){
	return list->tail;
}
