#include <stdio.h>
#include <stdlib.h>

typedef struct two_ind_t{
	int ind1;
	int ind2;
} two_ind_t;

two_ind_t* IsSumFound(int* arr, int size, int sum){
	two_ind_t *ret_val = (two_ind_t*)malloc(sizeof(two_ind_t));
	if(!ret_val) return NULL;
	ret_val->ind1 = -1;
	ret_val->ind2 = -1;
	
	if(size<2) return ret_val;
	
	int ind1=0, ind2=size-1;
	
	while(ind1!=ind2){
		int tmp = arr[ind1]+arr[ind2];
		if(sum==tmp) break;
		if(sum<arr[ind1]+arr[ind2]){
			ind2--;
			continue;
		} else {
			ind1++;
		}
	
	}
	if(ind1!=ind2){
		ret_val->ind1 = ind1;
		ret_val->ind2 = ind2;
	}
	return ret_val;
}

int main(){
	int arr[] = {2,4,7,10,12,14,23};
	int sum = 21;
	two_ind_t *ret_val = IsSumFound(arr,7,sum);
	printf("%d %d\n", ret_val->ind1, ret_val->ind2);
	free(ret_val);	
	
	return 0;	
}	
