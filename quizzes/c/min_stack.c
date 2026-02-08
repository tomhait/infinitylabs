#include <stdio.h>
#include <assert.h>
#include <stdlib.h>

/******************************************************************/

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

void stack_pop(stack *st)
{
	assert(st);
	if(!st->dummy->next) return;
	Node *nd = st->head;
	st->dummy->next = nd->next;
	st->head = st->dummy->next;
	free(nd);
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




/******************************************************************/
int is_min(void *val1, void *val2)
{
	return (*(int*)val1 <= *(int*)val2);
}

int is_equal(void *val1, void *val2)
{
	return (*(int*)val1 == *(int*)val2);
}

void min_push(stack* st, stack* min_st, void* val)
{
	stack_push(st, val);
	if(min_st->head == NULL || is_min(val, min_st->head->data))
	{
		stack_push(min_st, val);
	} 
}

void* min_pop(stack* st, stack* min_st)
{
	if(st->head == NULL) return NULL;
	
	void *val = st->head->data;
	stack_pop(st);
	if(min_st->head != NULL && is_equal(val, min_st->head->data))
	{
		stack_pop(min_st);
	}
	return val;
}

void* get_min(stack* min_st)
{
	if(min_st->head == NULL) return NULL;
	return min_st->head->data;
}

int main()
{
	int arr[] = {-1, 2, 3, 0};
	stack *st = stack_create(sizeof(arr[0]));
	stack *min_st = stack_create(sizeof(arr[0]));
	min_push(st, min_st, &arr[0]);
	min_push(st, min_st, &arr[1]);
	min_push(st, min_st, &arr[2]);
	min_push(st, min_st, &arr[3]);
	stack_print(st);
	stack_print(min_st);
	min_pop(st, min_st);
	stack_print(st);
	stack_print(min_st);
	min_pop(st, min_st);
	stack_print(st);
	stack_print(min_st);
	min_pop(st, min_st);
	stack_print(st);
	stack_print(min_st);
	min_pop(st, min_st);
	stack_print(st);
	stack_print(min_st);
	stack_print(st);
	stack_print(min_st);
	stack_destroy(st);	
	stack_destroy(min_st);
	return 0;
}
