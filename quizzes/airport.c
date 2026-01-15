#include <stdio.h>

int remaining_airplane(int land[], int land_size, int takeoff[], int take_size){
	int sum = 0;
	for(int i=0; i<land_size; i++) sum+=land[i];
	for(int i=0; i<take_size; i++) sum-=takeoff[i];
	
	return sum;
}

int remaining_airplane_single(int planes[], int size){
	for(int i=0; i<size-1; i++){
		int p1 = planes[i];
		if(p1==-1) continue;
		int match = 1;
		for(int j=i+1; j<size; j++){
			if(p1==planes[j] && planes[j]!=-1){
				match=2;
				planes[j] = -1;
			}
		}
		if(match!=2){
			return p1;
		} else {
			planes[i] = -1;
		}
	}
	if(planes[size-1]!=-1) return planes[size-1];
	return 0;
}

int main(){
	int land[] = {1234, 4321, 4566};
	int takeoff[] = {4566, 1234};
	int planes[] = {4321, 1234, 1234, 4566, 4321, 4566};
	printf("%d\n", remaining_airplane(land, 3, takeoff, 2));
	printf("%d\n", remaining_airplane_single(planes, 6));
	return 0;
}
