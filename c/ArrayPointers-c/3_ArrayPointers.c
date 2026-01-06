#include <stdio.h>
#include <stddef.h>

int main() {
    printf("Now int types:\n");	
    printf("Size of int:            %ld bytes\n", sizeof(int));
    printf("Size of unsigned int:   %ld bytes\n", sizeof(unsigned int));
    printf("Size of short int:      %ld bytes\n", sizeof(short int));
    printf("Size of unsigned short: %ld bytes\n", sizeof(unsigned short));
    printf("Size of long int:       %ld bytes\n", sizeof(long int));
    printf("Size of unsigned long:  %ld bytes\n", sizeof(unsigned long));
    printf("Size of long long int:  %ld bytes\n", sizeof(long long int));

    printf("\n\nNow floating point types:\n");    
    printf("Size of float:          %ld bytes\n", sizeof(float));
    printf("Size of double:         %ld bytes\n", sizeof(double));
    printf("Size of long double:    %ld bytes\n", sizeof(long double));

    
    printf("\n\nNow char types:\n");
    printf("Size of char:           %ld byte\n", sizeof(char));
    printf("Size of signed char:    %ld byte\n", sizeof(signed char));
    printf("Size of unsigned char:  %ld byte\n", sizeof(unsigned char));

    printf("\n\nNow NULL type:\n");
    printf("Size of void*:          %ld bytes\n", sizeof(void*));
    return 0;
}
