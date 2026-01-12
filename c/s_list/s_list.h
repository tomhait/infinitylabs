#include <stddef.h>

typedef struct sll_t sll_t;
typedef struct node_t node_t;
typedef void (*for_each_func)(void*);
typedef int (*match_func)(void*, ...);

sll_t* sll_create(void);
node_t* sll_append(sll_t* lst, void* data); // returns NULL for failure
node_t* sll_insert(sll_t* lst, node_t* node, void* data); // returns NULL for failure
void* sll_get_data(node_t* node);
void sll_set_data(node_t* node, void* data);
void* sll_pop(sll_tt* lst);
node_t* sll_get_next(node_t* node);
void sll_destroy(sll_t* lst);
size_t sll_get_count(const sll_t* lst);
int sll_remove(sll_t* lst, node_t* node);
int sll_forEach(sll_t* lst, for_each_func func);
node_t* sll_find(sll* list, void* param, match_func func); // returns NULL for failure


