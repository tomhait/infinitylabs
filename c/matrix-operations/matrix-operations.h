#include <stdlib.h>

typedef struct mat_t mat_t;

enum Status{
	FAILURE = 0,
	SUCCESS = 1,
	DIMENSIONS_ERROR = -1,
	NULL_PTR_ERROR = 2
};

enum Bool{
	FALSE,
	TRUE
};

mat_t* matrix_create(size_t rows, size_t cols);
void matrix_destroy(mat_t* matrix);
int matrix_add(const mat_t* matrix_a, const mat_t* matrix_b, mat_t* result);
int matrix_set(mat_t* matrix, double* elements, size_t size);
size_t matrix_get_num_of_rows(const mat_t* mat);
size_t matrix_get_num_of_cols(const mat_t* mat);
double matrix_get_val(const mat_t* matrix, const size_t row_idx, const size_t col_idx);
int matrix_multiply(const mat_t* matrix_a, const mat_t* matrix_b, mat_t* result);
int matrix_scalar_multiply(const mat_t* matrix, const double scalar, mat_t* result);
int matrix_is_same(const mat_t* matrix_a, const mat_t* matrix_b);
int matrix_transpose(const mat_t* matrix, mat_t* result);
double matrix_trace(const mat_t* matrix, int* status);
double matrix_determinant(const mat_t* matrix, int* status);
int matrix_get_submatrix(const mat_t* matrix, size_t row, size_t col, mat_t* result);
double matrix_norm(const mat_t* matrix);
int matrix_inverse(const mat_t* matrix, mat_t* result);


