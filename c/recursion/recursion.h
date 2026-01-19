typedef struct Node Node;
struct Node{
	int data;
	Node *next;
};

enum Bool{
	FALSE,
	TRUE
};

int Fibonacci(int element_index);
Node* FlipList(Node* node);
int RecStrlen(char *str);
int RecStrcmp(char* s1, char *s2);
int FindMult(int arr[], int size, int target);
//The function gets char str[], otherwise it won't work
void PrintPermut(char str[]);



