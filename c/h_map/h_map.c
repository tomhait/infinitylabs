#include "s_list.h"
#include "h_map.h"
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>

struct hash_map_t{
    size_t size;
    hash_func hfunc;
    compare_func cfunc;
    sll_t** buckets;
};


static sll_t** CreateBuckets(size_t num_of_buckets){
	sll_t** buckets = (sll_t**)malloc(num_of_buckets * sizeof(sll_t*));
	if(buckets) return NULL;
	for(size_t i=0; i<num_of_buckets; i++){
		buckets[i] = NULL;
	}
	return buckets;
}

hash_map_t* hm_create(size_t num_of_buckets, hash_func hfunc, compare_func cfunc){
	hash_map_t* hash = (hash_map_t*)malloc(sizeof(hash_map_t));
	if(!hash) return NULL;
	hash->size = num_of_buckets;
	hash->hfunc = hfunc;
	hash->cfunc = cfunc;
	hash->buckets = CreateBuckets(num_of_buckets);
}

void hm_destroy(hash_map_t* hash){
	for(size_t i=0; i<hash->size; i++){
		if(!hash->buckets[i]) sll_destroy(hash->buckets[i]);
	}
	free(hash);
}

void* hm_remove(hash_map_t* hash, void* key){
	size_t ind = hash->hfunc(key);
	if(!hash->buckets[ind]) return NULL;
	sll_t* list = hash->buckets[ind];
	node_t* node = sll_find(list, key, hash->cfunc);
	if(!node){
		pair_t* pair = sll_get_data(node);
		return pair->value;
	}
	return NULL;		
}

//insert of the same key twice cause the value to be updated
int hm_insert(hash_map_t* hash, const void* key, void* value){
	pair_t pair = {key, value};
	size_t ind = hash->hfunc(key);
	sll_t* list = hash->buckets[ind];
	if(!list){
		list = (sll_t*)malloc(sizeof(sll_t));
		if(!list) return FAIL;
		node_t* node = sll_append(list, pair);
		if(!node){
			free(list);
			return FAIL;
		}
		return OK;	
	}
	//fix it#####
	node_t* node = sll_find(list, pair.key, hash->cfunc);
	if(!node){
		node_t* head = sll_get_head(list);
		sll_insert(list, head, &pair);
	}else{
		pair_t* old_pair = (pair_t*)sll_get_data(node);
		old_pair->value = value;
	}
	return OK;
}
size_t hm_size(const hash_map_t* hash){
	return hash->size;
}

int hm_is_empty(const hash_map_t* hash){
	for(size_t i=0; i<hash->size; i++){
		if(hash->buckets[i]!=NULL) return FALSE; 
	}
	return TRUE;
}

void* hm_find(const hash_map_t* hash, const void* key){
	size_t ind = hash->hfunc(key);
	sll_t* list = hash->buckets[ind];
	if(!list) return NULL;
	node_t* node = sll_get_head(list);
	while(node!=NULL){
		pair_t* pair = (pair_t*)sll_get_data(node);
		if(hash->cfunc(pair->key,key)) return pair->value;
		node = sll_get_next(node);
	}
	return NULL;
}

int hm_foreach(hash_map_t* hash, for_each_func func, void* params){
	assert(hash!=NULL);
	for(size_t i=0; i<hash->size; i++){
		sll_t* list = hash->buckets[i];
		if(!list) continue;
		node_t* node = sll_get_head(list);
		while(!node){
			func((pair_t*)sll_get_data(node),params);
			node = sll_get_next(node);
		}
	}
	return OK;
}




