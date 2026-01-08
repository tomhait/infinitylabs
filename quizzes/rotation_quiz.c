#include <stdio.h>
#include <string.h>
#include <assert.h>

enum Status{
	FALSE,
	TRUE
};

/*int IsRotation(char *s1, char *s2){
	assert(strlen(s1)==strlen(s2));
	int len = strlen(s1);
	if(len==0) return TRUE;
	int count = 0;
	char prv = s1[0];
	char next = s1[1];
	int next_pos=1;
	while(count<len){
		int times = 1;
		for(int i=next_pos; i<len; i++){
			if(s1[i]==prv) times++;
		}
		for(int i=next_pos;i<len;i++){
			if(s1[i]!=prv){
				next=s1[i];
				next_pos=i+1;
				break;
			}
		}
		count+=times;
		for(int j=0;j<len;j++){
			if(s2[j]==prv) times--;
		}
		if(times!=0) return FALSE;
		prv=next;
	}
	if(count==len) return TRUE;
	return FALSE;
}*/

int IsRotation(char *s1, char *s2){
	assert(strlen(s1)==strlen(s2));
	int len = strlen(s1);
	if(len==0) return TRUE;
	for(int i=0; i<len;i++){
		int match = 1;
		for(int j=0; j<len; j++){
			if(s1[j]!=s2[(i+j)%len]){
				match=0;
				break;
			}
		}
		if(match) return TRUE;
	}
	return FALSE;
}
int main(){
	char *s1 = "12345";
	char *s2 = "45123";
	if(IsRotation(s1,s2)){
		printf("Success\n");
	} else {
		printf("Fail\n");
	}
	return 0;
}

	
	
