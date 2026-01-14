#include <stdio.h>

typedef struct bursa{
	int profit;
	int left;
	int right;
} bursa;

/*bursa Bursa(int *arr, int size){
	bursa ret = {0,0,size-1};
	int profit = arr[size-1] - arr[0];
	int left = 0, right = size-1;
	int best_left = 0, best_right = size-1;
	ret.profit = profit;
	
	while(left!=right){
		if(profit<arr[right]-arr[left+1]){
			left++;
			best_left=left;
			profit = arr[right]-arr[left];
			continue;
		} else if (profit < arr[right+1] - arr[left]){
			right++;
			best_right=right;
			profit = arr[right]-arr[left];
			continue;
		} else {
			left++;
			right++;
		}
	}
	
	ret.profit = arr[best_right] - arr[best_left];
	ret.left = best_left;
	ret.right = best_right;
	return ret;
}*/

bursa Bursa(int *arr, int size){
	bursa ret = {0,0,size-1};
	ret.profit = arr[size-1] - arr[0];
	int min_idx = 0;
	int cur_profit = ret.profit;
	
	for(int i= 1; i<size; i++){
		if(arr[i] < arr[min_idx]) min_idx = i;
		cur_profit = arr[i] - arr[min_idx];
		
		if(cur_profit > ret.profit){
			ret.profit = cur_profit;
			ret.left = min_idx;
			ret.right = i;
		}
	}
	return ret;
}

int main(){
	int arr[] = {6, 12, 3, 5, 1, 4, 9, 2};
	int size = sizeof(arr)/sizeof(arr[0]);
	bursa ret = Bursa(arr, size);
	printf("Profit is: %d\n",ret.profit);
	printf("But index is: %d\n",ret.left);
	printf("Sell index is: %d\n",ret.right);	
	return 0;
}
