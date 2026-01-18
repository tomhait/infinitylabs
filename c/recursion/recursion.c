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


