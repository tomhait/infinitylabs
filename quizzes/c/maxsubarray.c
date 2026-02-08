#include <stdio.h>

typedef struct result{
	int i;
	int j;
	int sum;
} result;

result MaxSubArray(int arr[], int size){
	int max_i=0, max_j=0, max_sum=0;
	int i=0, j=1, cur_sum=0;
	cur_sum = arr[i] + arr[j];
	max_sum = cur_sum;
	for(i=2; i < size; i++){
		if(cur_sum+arr[i] < arr[i]){
			cur_sum = arr[i];
			j=i;
		} else {
			cur_sum += arr[i];
		}
		if(cur_sum > max_sum){
			max_sum = cur_sum;
			max_i = j;
			max_j = i;
		}
	}
	result res = {max_i, max_j, max_sum};
	return res;
}

int main(){
	int arr[] = {-2, 1, -3, 4, -1, 2, 3, -5, 4};
	result res = MaxSubArray(arr, sizeof(arr)/sizeof(arr[0]));
	printf("%d %d %d\n", res.i, res.j, res.sum);
	return 0;
}
