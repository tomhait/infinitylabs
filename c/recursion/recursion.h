typedef struct Node Node;
struct Node{
	int data;
	Node *next;
};

enum Bool{
	FALSE,
	TRUE
};

long int Fibonacci(long int element_index);
long int IterFibonacci(long int element_index);
Node* FlipList(Node* node);
int RecStrlen(char *str);
int RecStrcmp(char* s1, char *s2);
int FindMult(int arr[], int size, int target);
//The function gets char str[], otherwise it won't work
void PrintPermut(char str[]);



