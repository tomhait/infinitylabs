#include <stdio.h>

float MyTenPow(int n){
	float result = 1.0;
	int i;
	int abs_n = (n<0) ? -n : n;
	
	for(i=0; i<abs_n; ++i){
		if(n>=0){
			result *= 10;
		} else {
			result /= 10;
		}
	}
	
	return result; 
}

int main(){
	int n;
	float result;
	printf("Enter exponent n: ");
	scanf("%d",&n);
	result = MyTenPow(n);
	printf("10 to the power of %d is: %.2f\n",n,result);
	return 0;
}
