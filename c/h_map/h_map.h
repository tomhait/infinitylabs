#include <stddef.h>

typedef struct hash_map_t hash_map_t;    
typedef int(*for_each_func)(void*, void*);
typedef size_t(*hash_func)(void*);
typedef int(*compare_func)(void*, void*);

enum Status{
	FAIL,
	OK
};

enum Bool{
	FALSE,
	TRUE
};

typedef struct pair_t{
    void* key;
    void* value;
} pair_t;

hash_map_t* hm_create(size_t num_of_buckets, hash_func hfunc, compare_func cfunc);
void hm_destroy(hash_map_t* hash);
void* hm_remove(hash_map_t* hash, void* key);
int hm_insert(hash_map_t* hash, const void* key, void* value);//insert of the same key twice cause the value to be updated
size_t hm_size(const hash_map_t* hash);
int hm_is_empty(const hash_map_t* hash);
void* hm_find(const hash_map_t* hash, const void* key);
int hm_foreach(hash_map_t* hash, for_each_func func, void* params);

