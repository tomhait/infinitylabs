typedef struct Node Node;
struct Node{
	int data;
	Node *next;
};

int Fibonacci(int element_index);
Node* FlipList(Node* node);
int RecStrlen(char *str);
int RecStrcmp(char* s1, char *s2);



