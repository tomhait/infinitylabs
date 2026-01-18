#include <stddef.h>

typedef struct hash_map_t hash_map_t;    
typedef int(*hm_for_each_func)(void*, void*);
typedef size_t(*hash_func)(void*);
typedef int(*compare_func)(void*, void*);

enum Bool{
	FALSE,
	TRUE
};

typedef struct pair_t{
    const void* key;
    void* value;
} pair_t;

/*
* Creates hash map containing with num_of_buckets buckets
* hfunc - hash function
* cfunc - keys comparison function
* Returns - pointer to hash map
*/
hash_map_t* hm_create(size_t num_of_buckets, hash_func hfunc, compare_func cfunc);

/*
* Frees the hash map
* O(n) time complexity (n number of pairs in the hash map)
*/
void hm_destroy(hash_map_t* hash);

/*
* Removes a key-value pair by searching the key in the hash map
* Returns the removed value (NULL key-value not found in the hash)
* O(1) Amortized time complexity (O(n) worst case)
*/
void* hm_remove(hash_map_t* hash, void* key);

/*
* Inserts a key-value pair to the hash map
* If the key is already in the hash map - replaces its associated value with the new value in key_value
* O(1) Amortized time complexity (O(n) worst case)
*/
int hm_insert(hash_map_t* hash, pair_t* key_value);

/*
* Returns the number of buckets in the hash map
* O(1) time complexity
*/
size_t hm_size(const hash_map_t* hash);

/*
* Returns TRUE is at least one key-value pair is in the hash map
* O(1) Amortized time complexity (O(n) worst case)
*/
int hm_is_empty(const hash_map_t* hash);

/*
* Returns the associated value of the key in the hash map (NULL is key not found in the hash map)
* O(1) Amortized time complexity (O(n) worst case)
*/
void* hm_find(const hash_map_t* hash, const void* key);

/*
* Apllies "for each" on every key-value pair_t in the hash using func and param
* O(n) Time complexity
*/
int hm_foreach(hash_map_t* hash, hm_for_each_func func, void* params);

