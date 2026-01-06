#include <stdio.h>

void SumRows(int rows, int cols, int arr[rows][cols], int *row_sums){
	for(int i=0;i<rows;i++){
		int sum_row = 0;
		for(int j=0;j<cols;j++){
			sum_row+=arr[i][j];
		}
		row_sums[i] = sum_row;
	}
}

int main(){
	int rows=2, cols=3;
	int arr[2][3] = {{1, 2, 3}, {4, 5, 6}};
	int row_sums[2];
	SumRows(rows,cols,arr,row_sums);
	for(int i=0; i<rows; i++){
		printf("Sum of row %d is: %d\n",i+1,row_sums[i]);
	}
	return 0;
}
