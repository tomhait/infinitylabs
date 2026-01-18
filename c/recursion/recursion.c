#include "recursion.h"
#include <stdio.h>
#include <stddef.h>
#include <assert.h>

int Fibonacci(int element_index)
{
	if(element_index==0) return 0;
	if(element_index==1) return 1;
	return Fibonacci(element_index-1)+Fibonacci(element_index-2);
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


