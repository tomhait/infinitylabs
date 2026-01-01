#include <stdio.h>

void swapTwoNums(double *first, double *second){
	*first = *first - *second;
	*second = *first + *second;
	*first = *second - *first;
}

int main(){
	double first, second;
	printf("Enter a: ");
	scanf("%lf",&first);
	printf("Enter b: ");
	scanf("%lf",&second);
	swapTwoNums(&first, &second);
	printf("After swapping\n");
	printf("a = %.2lf\n", first);
	printf("b = %.2lf\n", second);
	return 0;
}
