#include "s_list.h"
#include "h_map.h"
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>

#define LOAD_FACTOR 0.75
#define GROWTH_FACTOR 2

struct hash_map_t{
    size_t num_of_buckets;
    size_t current_filled_buckets;
    hash_func hfunc;
    compare_func cfunc;
    sll_t** buckets;
};

static size_t ComputeHashIndex(size_t hash, size_t table_size){
	return hash % table_size;
}

static sll_t** CreateBuckets(size_t num_of_buckets){
	sll_t** buckets = (sll_t**)malloc(num_of_buckets * sizeof(sll_t*));
	if(!buckets) return NULL;
	for(size_t i=0; i<num_of_buckets; i++){
		buckets[i] = NULL;
	}
	return buckets;
}

hash_map_t* hm_create(size_t num_of_buckets, hash_func hfunc, compare_func cfunc){
	hash_map_t* hash = (hash_map_t*)malloc(sizeof(hash_map_t));
	if(!hash) return NULL;
	hash->num_of_buckets = num_of_buckets;
	hash->current_filled_buckets=0;
	hash->hfunc = hfunc;
	hash->cfunc = cfunc;
	hash->buckets = CreateBuckets(num_of_buckets);
	return hash;
}

void hm_destroy(hash_map_t* hash){
	assert(hash);
	for(size_t i=0; i<hash->num_of_buckets; i++){
		sll_t *list = hash->buckets[i];
		if(list!=NULL){
			size_t list_count = sll_get_count(list);
			node_t *node = sll_get_head(list);
			for(size_t j=0; j<list_count; j++){
				free(sll_get_data(node));
				node = sll_get_next(node);
			}
			sll_destroy(list);
		}
	}
	free(hash->buckets);
	free(hash);
}

void* hm_remove(hash_map_t* hash, void* key){
	size_t ind = ComputeHashIndex(hash->hfunc(key), hash->num_of_buckets);
	if(!hash->buckets[ind]) return NULL;
	sll_t* list = hash->buckets[ind];
	pair_t find_pair = {key, key};
	node_t* node = sll_find(list, &find_pair, hash->cfunc);
	if(node!=NULL){
		pair_t* pair = sll_get_data(node);
		void *value = pair->value;
		free(pair);
		pair = NULL;
		sll_remove(list, node);
		if(sll_get_count(list)==0){
			sll_destroy(list);
			hash->buckets[ind] = NULL;
			hash->current_filled_buckets--;
		}
		return value;
	}
	return NULL;		
}

static int resize_hash(hash_map_t *hash){
	size_t old_capacity = hash->num_of_buckets;
	size_t new_capacity = old_capacity * GROWTH_FACTOR;
	sll_t **new_buckets = CreateBuckets(new_capacity);
	if(!new_buckets) return FAIL;
	sll_t **old_buckets = hash->buckets;
	hash->buckets = new_buckets;
	hash->current_filled_buckets = 0;
	hash->num_of_buckets = new_capacity;
	for(size_t i=0; i<old_capacity; i++){
		sll_t *list = old_buckets[i];
		if(list!=NULL){
			size_t list_count = sll_get_count(list);
			node_t *node = sll_get_head(list);
			for(size_t j=0; j<list_count; j++){
				pair_t* pair = sll_get_data(node);
				hm_insert(hash, pair);
				free(pair);
				node = sll_get_next(node);
			}
			sll_destroy(list);
		}
	}
	free(old_buckets);
	return OK;
}

int hm_insert(hash_map_t* hash, pair_t* key_value){
	assert(hash);
	assert(key_value);
	void *non_const_key = (void*)(key_value->key);
	size_t ind = ComputeHashIndex(hash->hfunc(non_const_key), hash->num_of_buckets);
	pair_t *pair = (pair_t*)malloc(sizeof(pair_t));
	if(!pair) return FAIL;
	pair->key = key_value->key;
	pair->value = key_value->value;
	sll_t* list = hash->buckets[ind];
	if(!list){
		list = sll_create();
		if(!list) return FAIL;
		node_t* node = sll_append(list, pair);
		if(!node){
			free(list);
			return FAIL;
		}
		hash->buckets[ind] = list;
		hash->current_filled_buckets++;
		double curr_load_factor = (double)hash->current_filled_buckets / hash->num_of_buckets;
		if(curr_load_factor > LOAD_FACTOR){
			resize_hash(hash);
		}
		return OK;	
	}
	node_t* node = sll_find(list, pair, hash->cfunc);
	if(!node){
		node_t* head = sll_get_head(list);
		sll_insert(list, head, pair);
	}else{
		pair_t* old_pair = (pair_t*)sll_get_data(node);
		old_pair->value = pair->value;
		free(pair);
	}
	return OK;
}
size_t hm_size(const hash_map_t* hash){
	assert(hash);
	return hash->num_of_buckets;
}

int hm_is_empty(const hash_map_t* hash){
	assert(hash);
	if(hash->current_filled_buckets > 0) return FALSE;
	return TRUE;
}

void* hm_find(const hash_map_t* hash, const void* key){
	assert(hash);
	void *non_const_key = (void*)key;
	size_t ind = ComputeHashIndex(hash->hfunc(non_const_key), hash->num_of_buckets);
	sll_t* list = hash->buckets[ind];
	if(!list) return NULL;
	node_t* node = sll_get_head(list);
	size_t list_count = sll_get_count(list);
	for(size_t j=0; j<list_count; j++){
		pair_t* pair = (pair_t*)sll_get_data(node);
		pair_t ref = {non_const_key,NULL};
		if(hash->cfunc(pair,&ref)){
			sll_remove(list, node);
			node_t *head = sll_get_head(list);
			if(!head){
				sll_append(list,pair);
			} else sll_insert(list, sll_get_head(list), pair);
			return pair->value;
		}
		node = sll_get_next(node);
	}
	return NULL;
}

int hm_foreach(hash_map_t* hash, hm_for_each_func func, void* params){
	assert(hash);
	for(size_t i=0; i<hash->num_of_buckets; i++){
		sll_t* list = hash->buckets[i];
		if(!list) continue;
		node_t* node = sll_get_head(list);
		size_t list_count = sll_get_count(list);
		for(size_t j=0; j<list_count; j++){
			func((pair_t*)sll_get_data(node),params);
			node = sll_get_next(node);
		}
	}
	return OK;
}




