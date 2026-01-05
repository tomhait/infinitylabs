#include "pointers.h"

int main(){
	printf("Exercise 1 test:\n");
	int x = 10, y = 20;
	SwapInts(&x,&y);
	(x == 20 && y == 10) ? printf("Yay\n"):printf("Nay\n");
	printf("Exercise 2 test:\n");
	size_t sx = 10, sy = 20;
	SwapSizeT(&sx,&sy);
	(sx == 20 && sy == 10) ? printf("Yay\n"):printf("Nay\n");	
	size_t *p1 = &sx, *p2 = &sy;
	SwapSizeTpo(&p1,&p2);
	(p1 == &sy && p2 == &sx) ? printf("Yay\n"):printf("Nay\n");
	
	printf("Exercise 3 test strcpy:\n");
	char s1[] = "Test strcpy";
	char dest[MAX_SIZE];
	strcpy(dest,s1);
	printf("%s, %s, Yay?",s1,dest);
	
	printf("Exercise 3 test strdup:\n");
	char s2[] = "Test strdup";
	char *duplicate = strdup(s2);
	if(duplicate != NULL){
		printf("%s, %s, Yay?",s2,duplicate);
		free(duplicate);
	}else printf("strdup: failed to allocate memory\n");
	
	printf("Advanced exercise 1, Naive strstr:\n");
	char *needle = "test";
	char *haystack= "findMytestBla";
	char *h = strstrNaive(haystack, needle);
	printf("First occurence of %s found in: %s\n", needle, h);
	 
	return 0;
}
