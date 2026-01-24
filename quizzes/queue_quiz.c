#include <stdio.h>
#include <stddef.h>
#include <assert.h>
#include <string.h>
#include <stdlib.h>

/******************************************************/

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
	nd->data = val;
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

void* stack_pop(stack *st)
{
	assert(st);
	if(!st->dummy->next) return NULL;
	Node *nd = st->head;
	st->dummy->next = nd->next;
	st->head = st->dummy->next;
	void *val = nd->data;
	free(nd);
	return val;
}

void stack_destroy(stack *st)
{
	assert(st);
	while(st->dummy->next!=NULL)
	{
		Node *nd = st->head;
		st->dummy->next = nd->next;
		st->head = nd->next;
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
	printf("\n\n\n");
}

/******************************************************/
void enqueue(stack* in, void* data)
{
	assert(in);
	stack_push(in, data);
}

void* dequeue(stack* in, stack* out)
{
	assert(in);
	assert(out);
	
	if(!out->head)
	{
		if(!in->head)
		{
			return NULL;
		}
		while(in->head != NULL)
		{
			void *val = stack_pop(in);
			stack_push(out, val);
		}
	}
	void *val = stack_pop(out);
	return val;
}

int main()
{
	int arr[] = {1, 2, 3, 4, 5, 6};
	stack *in = stack_create(sizeof(arr[0]));
	stack *out = stack_create(sizeof(arr[0]));
	enqueue(in, &arr[0]);
	enqueue(in, &arr[1]);
	enqueue(in, &arr[2]);
	enqueue(in, &arr[3]);
	stack_print(in);
	dequeue(in, out);
	stack_print(in);
	stack_print(out);
	dequeue(in, out);
	stack_print(in);
	stack_print(out);
	enqueue(in, &arr[4]);
	enqueue(in, &arr[5]);
	stack_print(in);
	dequeue(in, out);
	stack_print(in);
	stack_print(out);
	stack_destroy(in);
	stack_destroy(out);	
	return 0;
}

