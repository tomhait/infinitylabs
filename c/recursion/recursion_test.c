#include "recursion.h"
#include <stdio.h>

int main()
{
	int index = 6;
	printf("Fibonacci value of index %d is: %d\n", index, Fibonacci(index));
	
	Node nd1 = {1, NULL};
	Node nd2 = {2, NULL};
	Node nd3 = {3, NULL};
	nd1.next = &nd2;
	nd2.next = &nd3;
	Node *head = &nd1;
	printf("Previous order of nodes: %d %d %d\n", head->data, head->next->data, head->next->next->data);
	head = FlipList(&nd1);
	printf("Current order of nodes: %d %d %d\n", head->data, head->next->data, head->next->next->data);
	
	char *str = "Tom";
	printf("The recursive length of %s is: %d\n", str, RecStrlen(str));
	
	char *s1 = "TomH";
	char *s2 = "Tom";
	int comp = RecStrcmp(s1,s2);
	if(comp==0)
	{
		printf("%s and %s are the same\n",s1, s2);
	} else if( comp > 0)
	{
		printf("%s is bigger than %s\n",s1, s2);
	} else 
	{
		printf("%s is smaller than %s\n",s1, s2);
	}
	
	int arr[] = {5,7};
	int target = 28;
	if(FindMult(arr, sizeof(arr)/sizeof(arr[0]), target))
	{
		printf("Found a multiplication\n");
	} else {
		printf("Did not find a multiplication\n");
	}
	char s[] = "Tom";
	PrintPermut(s);
	return 0;
}

