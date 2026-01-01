#include <stdio.h>

int flipDigitOrder(int digits){
	int digitsReversed = 0;
	int abs_digits = (digits<0) ? -digits : digits;
	while(abs_digits>0){
		digitsReversed = digitsReversed*10 + abs_digits%10;
		abs_digits/=10;
	}
	if(digits<0) digitsReversed=-digitsReversed;
	return digitsReversed;
}


int main(){
	int digits, digitsReversed;
	printf("Enter an int number to flip order: ");
	scanf("%d",&digits);
	digitsReversed = flipDigitOrder(digits);
	printf("The flipped order of %d is: %d\n", digits, digitsReversed);
	return 0;
}
