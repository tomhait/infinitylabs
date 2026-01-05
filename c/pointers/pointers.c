#include "pointers.h"

void SwapInts(int *x, int *y){
	int tmp = *x;
	*x = *y;
	*y = tmp;
}

void SwapSizeT(size_t *x, size_t *y){
	size_t temp = *x;
	*x = *y;
	*y = temp;
}

void SwapSizeTpo(size_t **x, size_t **y){
	SwapSizeT((size_t *)x, (size_t *)y);
}

char *strcpy(char* dest, const char* source){
	assert(source != NULL);
	assert(dest != NULL);
	char *last=dest;
	while((*dest++ = *source++) != '\0'){}
	return last;
}

char *strdup(const char *s){
	assert(s!=NULL);
	
	int len = 0;
	while(s[len]!='\0') len++;
	
	char *str_cp = (char *)malloc(len+1); //+1 for null terminator
	
	//check if failed allocation
	if(str_cp==NULL) return NULL;
	
	return strcpy(str_cp, s);
}

/*Advanced Exercises*/
char *strstrNaive(const char *haystack, const char *needle){
	assert(haystack!=NULL);
	assert(needle!=NULL);
	
	if(!*needle) return (char*)haystack;
	
	const char *h = haystack;
	
	while(*h!='\0'){
		char *h_ptr = h;
		char *n_ptr = needle;
		
		while(*h_ptr!='\0' && *n_ptr!='\0' && *h_ptr == *n_ptr){
			h_ptr++;
			n_ptr++;
		}
		if(*n_ptr=='\0') return (chr*)h; //match
		h++;
	}
	return NULL;
}
char *strstrKMP(const char *haystack, const char *needle){
	return NULL;
}

