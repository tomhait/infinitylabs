#include "ArrayPointers.h"
#include <stdio.h>
#include <assert.h>

int main(){
	printf("Test exercise 1:\n");
	int rows=2, cols=3;
        int arr[2][3] = {{1, 2, 3}, {4, 5, 6}};
        int row_sums[2];
        SumRows(rows,cols,arr,row_sums);
	assert(row_sums[0]==6);
	assert(row_sums[1]==15);
	printf("\n\n\n***************************\n\n\n");
	printf("Test exercise 2:\n");
	assert(Josephus(100,1)==73);
	assert(Josephus(7,1)==7);
	assert(Josephus(7,2)==1);
	printf("\n\n\n***************************\n\n\n");	
	printf("Run exercise 3:\n");
	PrintSizeofDataTypes();
	printf("\n\n\n***************************\n\n\n");
	printf("Run exercise 4:\n");
	UpperToLowerEnviron();
	return 0;
}
