#include <stdio.h>
#include <stddef.h>
#include <assert.h>
#include <string.h>
#include <stdlib.h>

typedef struct Node{
	void *data;
	struct Node* next;
} Node;

typedef struct stack{
	Node *dummy;
	Node *head;
	size_t var_size;
} stack;

enum Status{
	FAIL,
	SUCCESS
};

stack* stack_create(size_t var_size)
{
	stack *st = malloc(sizeof(stack));
	if(!st) return NULL;
	st->var_size = var_size;
	st->head= NULL;
	st->dummy = malloc(sizeof(Node));
	if(!st->dummy){
		free(st);
		return NULL;
	}
	st->dummy->next = NULL;
	return st;
}

int stack_push(stack *st, void *val)
{
	assert(st);
	Node *nd = malloc(sizeof(Node));
	if(!nd) return FAIL;
	nd->data = malloc(sizeof(st->var_size));
	if(!nd->data) return FAIL;
	memcpy(nd->data, val, st->var_size);
	if(!st->head){
		st->head = nd;
		nd->next = NULL;
		st->dummy->next = st->head;
	} else {
		nd->next = st->head;
		st->dummy->next = nd;
		st->head = nd;
	}
	return SUCCESS;
}

void stack_pop(stack *st)
{
	assert(st);
	if(!st->dummy->next) return;
	Node *nd = st->head;
	st->dummy->next = nd->next;
	st->head = st->dummy->next;
	//void *val = nd->data;
	free(nd->data);
	free(nd);
	//return val;
}

void stack_destroy(stack *st)
{
	assert(st);
	while(st->dummy->next!=NULL)
	{
		Node *nd = st->head;
		st->dummy->next = nd->next;
		st->head = nd->next;
		free(nd->data);
		free(nd);
	}
	free(st->dummy);
	free(st);
}

void stack_print(stack *st)
{
	assert(st);
	Node *nd = st->head;
	while(nd!=NULL){
		printf("%d\n",*((int*)nd->data));
		nd = nd->next;
	}
}

int main()
{
	int arr[] = {1, 2, 3};
	stack *st = stack_create(sizeof(arr[0]));
	stack_push(st, &arr[0]);
	stack_push(st, &arr[1]);
	stack_push(st, &arr[2]);
	stack_print(st);
	
	stack_pop(st);
	stack_print(st);
	stack_pop(st);
	stack_print(st);
	stack_destroy(st);	
	return 0;
}
