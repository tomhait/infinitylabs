#include "h_map.h"
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <string.h>

#define DICT_PATH "/usr/share/dict/words"
#define WORD_LEN 50
#define HASH_DICT_SIZE 200
#define UNUSED(x) (void)(x)

void load_linux_dic(hash_map_t *dict){
	FILE *fp = fopen(DICT_PATH,"r");
	if(!fp) return;
	char word[WORD_LEN];
	while(fgets(word, sizeof(word), fp)){
		word[strcspn(word, "\n")] = 0;
		char *key = strdup(word);
		pair_t pair = {key, key};
		hm_insert(dict, &pair);
	}
	fclose(fp);
}

void free_dict(hash_map_t *dict){
	FILE *fp = fopen(DICT_PATH,"r");
	if(!fp) return;
	char word[WORD_LEN];
	while(fgets(word, sizeof(word), fp)){
		word[strcspn(word, "\n")] = 0;
		void *key = hm_remove(dict, word);
		if(key!=NULL){
			free(key);
		}
	}	
}

int PrintPair(void* pair, void* params){
	UNUSED(params);
	printf("Key: %s, Value: %d\n",(char*)(((pair_t*)pair)->key), *(int*)(((pair_t*)pair)->value));
	return 0;
}

size_t djb2_hash(void *key){
	size_t hash = 5381;
	int c;
	unsigned char *str = (unsigned char*)key;
	while((c = *str++)){
		//hash*33 + c
		hash = ((hash << 5) + hash) + c;
	}
	
	return hash;
}

size_t Int_hash(void *key){
	return (size_t)(*(int*)key);
}

int StrCompare(void* pair1, void* pair2){
	pair_t *p1 = (pair_t*)pair1;
	pair_t *p2 = (pair_t*)pair2;	
	return strcmp((char*)(p1->key), (char*)(p2->key))==0;
}

int spell_checker(){
	hash_map_t *dict = hm_create(HASH_DICT_SIZE, djb2_hash, StrCompare);
	load_linux_dic(dict);
	char word[WORD_LEN];
	int userInput = 0;
	while(1){
		printf("Enter 0 to terminate\n");
		scanf("%d", &userInput);
		if(userInput==0) break;
		while(getchar() != '\n');
		printf("Type a word to verify if it's in the Linux dictionary: ");
		if(fgets(word, sizeof(word), stdin)) word[strcspn(word, "\n")] = 0;
		char *value = hm_find(dict, word);
		if(!value){
			printf("%s is not in the dictionary\n", word);
		} else printf("%s is in the dictionary\n", word);
	}
	free_dict(dict);
	hm_destroy(dict);
	return TRUE;
}

int IntCompare(void* pair1, void* pair2){
	int val1 = *(int*)((pair_t*)pair1)->key;
	int val2 = *(int*)((pair_t*)pair2)->key;
	return val1 == val2;
}

int IsSumFound(int arr[], size_t size, int target){
	hash_map_t *hash = hm_create(size, Int_hash, IntCompare);
	int flag = FALSE;
	int *ind = (int*)malloc(size*sizeof(int));
	if(!ind) return FALSE;
	for(size_t j = 0; j<size; j++) ind[j] = j;
	for(size_t i=0; i<size; i++){
		int diff = target - arr[i];
		int *value = (int*)hm_find(hash, &diff);
		if( value != NULL){
			printf("The indices are: %d (%d) and %ld (%d)\n", *value, arr[*value], i, arr[i]);
			flag = TRUE;
			break;
		}
		pair_t pair = {&arr[i], &ind[i]};
		hm_insert(hash, &pair);
	}
	free(ind);
	hm_destroy(hash);
	if(!flag) printf("No indices found\n");
	return flag;	

}

void testIsSumFound(){
	int arr[] = {2, 4, 7, 10, 12, 14, 23};
	size_t size = sizeof(arr)/sizeof(arr[0]);
	int target = 21;
	IsSumFound(arr, size, target);
}

void testHash(){
	int ages[] = {30, 27, 26, 40};
	pair_t p1 = {"tom", &ages[0]};
	pair_t p2 = {"gabi", &ages[1]};
	pair_t p3 = {"moshe", &ages[2]};
	hash_map_t* hm = hm_create(3, djb2_hash, StrCompare);
	hm_insert(hm, &p1);
	hm_insert(hm, &p2);
	hm_insert(hm, &p3);
	assert(hm_size(hm) == 3);
	int *value = (int*)(hm_find(hm, p2.key));
	assert(value);
	assert(value == p2.value);
	hm_foreach(hm, PrintPair, NULL);
	pair_t p4 = {"tom", &ages[3]};
	hm_insert(hm, &p4);
	printf("\n\n\n");
	hm_foreach(hm, PrintPair, NULL);
	pair_t p5 = {"Hertzel", &ages[3]};
	hm_insert(hm, &p5);
	printf("\n\n\n");
	hm_foreach(hm, PrintPair, NULL);
	hm_destroy(hm);
}

int main(){
	spell_checker();
	testIsSumFound();
	testHash();
	return 0;
}
