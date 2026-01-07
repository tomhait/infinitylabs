#ifndef ARRAY_POINTERS
#define ARRAY_POINTERS
#include <stddef.h>

/*
* Exercise 1 functions
*/
/*
* Helper function to sum rows of a matrix
*/
void SumRows(int rows, int cols, int arr[rows][cols], int *row_sums);

/*
*Exercise 2 functions:
*/
int LastSoldierNaive(size_t size, size_t k);
int LastSoldierN(size_t size, size_t k);
int FindNextAlive(size_t alive[], size_t cur_soldier, size_t size);


/*
*Exercise 3 functions:
*/

void PrintSizeofDataTypes();

/*
*Exercise 4 functions:
*/
char** GetBuffer();
int SetLowEnviron(char* environ);
int UpperToLowerEnviron();

#endif
