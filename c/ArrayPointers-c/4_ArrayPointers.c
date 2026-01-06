#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <stdlib.h>

extern char **environ;

char** GetBuffer(){
	int count = 0;
	while(environ[count]!=NULL) count++;
	char **low_environ = (char **)malloc((count+1)*sizeof(char *));
	if(low_environ==NULL){
		perror("Failed to allocate buffer");
		return NULL;
	}
	return low_environ;
}

int main(){
	int i=0, count=0;
	const char *delim = "=";
	char **low_environ = GetBuffer();
	if(low_environ == NULL) return 1;
	while(environ[count]!=NULL) count++;
		
	for(i=0; i < count; i++){
		char *token = strtok(environ[i],delim);
		int len = strlen(token);
		low_environ[i]=(char *)malloc((len+1)*sizeof(char));
		if(low_environ[i]==NULL){
			perror("Failed to allocate string memory");
			return 1;
		}
		for(int j=0; j<len; j++){
			low_environ[i][j] = tolower((unsigned char)token[j]);
		}
		low_environ[i][len] = '\0';
	}
	low_environ[count] = NULL;
	
	printf("Lowercase Enviroment Variables:\n");
	for(int j=0; j<count; j++) printf("%s\n", low_environ[j]);
	
	for(int j=0; j<count; j++) free(low_environ[j]);
	free(low_environ);
	return 0;
}
