#include "recursion.h"
#include <stdio.h>
#include <stddef.h>
#include <assert.h>

long int Fibonacci(long int element_index)
{
	if(element_index<=1) return element_index;
	return Fibonacci(element_index-1)+Fibonacci(element_index-2);
}

long int IterFibonacci(long int element_index)
{
	if(element_index<=1) return element_index;
	long int a = 0;
	long int b = 1;
	long int c = 0;
	for(long int i=1; i < element_index; i++)
	{
		c = a + b;
		a = b;
		b = c;
	}
	return b;
}

Node* FlipList(Node* node){
	if(!node || node->next == NULL) return node;
	
	Node* head = FlipList(node->next);
	node->next->next = node;
	node->next = NULL;
	
	return head;
}

int RecStrlen(char *str){
	if(*str == '\0') return 0;
	return RecStrlen(str+1) + 1;
}

int RecStrcmp(char* s1, char *s2){
	if(*s1 == *s2) 
	{
		if(*s1 == '\0') 
		{
			return 0;
		}
		return 	RecStrcmp(s1 + 1, s2 + 1);
	}
	
	return *(unsigned char*)s1 - *(unsigned char*)s2;		
}

int FindMult(int arr[], int size, int target){
	if(target == 1) return TRUE;
	for(int i=0; i < size; i++)
	{
		if(arr[i] <= 1)
		{
			if(arr[i] == target) return TRUE;
			continue;
		}
		if(target % arr[i] == 0)
		{
			return FindMult(arr, size, target / arr[i]);
		}
	}
	return FALSE;
}

static void Swap(char *x, char *y){
	char temp = *x;
	*x = *y;
	*y = temp;
}

static void PrintPermHelper(char str[], int start, int end){
	if(start == end) {
		printf("%s\n", str);
		return;
	}
	for(int i=start; i<end; i++)
	{
		Swap(str+start, str+i);
		PrintPermHelper(str, start+1, end);
		Swap(str+start, str+i);
	}
}

void PrintPermut(char str[]){
	PrintPermHelper(str, 0, RecStrlen(str));	
}

