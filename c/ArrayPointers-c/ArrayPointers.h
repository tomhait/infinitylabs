#ifndef ARRAY_POINTERS
#define ARRAY_POINTERS

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
int LastSoldierNaive(int size, int k);
int LastSoldierN(int size, int k);
int FindNextAlive(int alive[], int cur_soldier, int size);


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
