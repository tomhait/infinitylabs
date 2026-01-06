#include <stdio.h>
#include <stdlib.h>

/*
* k - first knife holder
* size - number of soldiers in the circle
*/
int LastSoldier(int size, int k){
	int *alive = (int*)calloc(size+1, sizeof(int));
	int lastAlive = 0;
	int remaining = size;
	int cur_holder = k;//soldier with the knife
	
	for(int i=1; i<=size; i++){
		alive[i] = 1;
	}
	
	while(remaining > 1){
		int victim = (cur_holder % size)+1;
		while(alive[victim] == 0) victim = (victim % size)+1;
		alive[victim] = 0;
		//printf("killed %d\n", victim); for testing
		remaining--;
		
		if(remaining==1) break;
		
		int next_holder = (victim % size) + 1;
		while(alive[next_holder] == 0) next_holder = (next_holder % size)+1;
		cur_holder = next_holder;
	}
	for(int i=1; i<=size; i++){
		if(alive[i] == 1){
			lastAlive=i;
			break;
		}
	}
	
	free(alive);
	
	return lastAlive;
}

int main(){
	int size = 100, k = 1;
	printf("The last survivor is: %d\n", LastSoldier(size, k));
	return 0;
}
