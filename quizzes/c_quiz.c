#include <stdio.h>
#include <string.h>
#include <ctype.h>

void TF(int num){
	int i=1;
	
	for(; i<=num; i++){
		int flag = 0;
		if(i%3==0){
			printf("T");
			flag=1;
		}
		if(i%5==0){
			printf("F");
			flag=1;
		}
		if(flag==0) printf("%d",i);
		printf("\n");
	}
}

void low_reverse(char *str){
	int size = strlen(str);
	int i=0;
	
	for(; i<size/2; i++){
		char first = tolower((unsigned char)str[i]);
		char last = tolower((unsigned char)str[size-i-1]);
		str[i] = last;
		str[size-i-1] = first;
	}
	if(size%2!=0){
		str[size/2] = tolower((unsigned char)str[size/2]);
	}
}


int main(){
	int num = 20;
	char str[] = "HelLo wORLdE";
	
	printf("Test TF:\n");
	TF(num);
	
	printf("Test low reverse:\n");
	low_reverse(str);
	printf("%s\n", str);
	
	return 0;
}

