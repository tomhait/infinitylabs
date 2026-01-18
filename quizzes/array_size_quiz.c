#include <stdio.h>
#include <stdlib.h>
#include <assert.h>

int My_strlen(char *str){
	assert(str);
	int len = 0;
	while(*str++!='\0') len++;
	return len;
}

int My_rand_bytes(){
	int size = rand()%100;
	int *arr = (int*)malloc(sizeof(int)*size);
	int bytes = sizeof(arr[0])*size;
	free(arr);
	return bytes;
}

int My_fixed_bytes(int arr[], int size){
	assert(arr);
	return size*sizeof(int);	
}

int main(){
	char *str = "Tom";
	int arr[] = {0,1,2};
	printf("strlen %d\n",My_strlen(str));
	printf("rand bytes %d\n",My_rand_bytes());
	printf("Fixed bytes %d\n",My_fixed_bytes(arr,sizeof(arr)/sizeof(arr[0])));
	return 0;
}

