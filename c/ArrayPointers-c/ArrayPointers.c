#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <stdlib.h>
#include <assert.h>

/*********************************Exercise 1**************************************/
void SumRows(int rows, int cols, int arr[rows][cols], int *row_sums){
        for(int i=0;i<rows;i++){
                int sum_row = 0;
                for(int j=0;j<cols;j++){
                        sum_row+=arr[i][j];
                }
                row_sums[i] = sum_row;
        }
}

/*********************************Exercise 2**************************************/
enum Status {
	DEAD,
	ALIVE
};

int FindNextAlive(int alive[], int cur_soldier, int size){
	int next_alive = (cur_soldier % size)+1;
        while(alive[next_alive] == DEAD) next_alive = (next_alive % size)+1;
        return next_alive;
}

int LastSoldierNaive(int size, int k){
	int *alive = (int*)calloc(size+1, sizeof(int));
	assert(alive!=NULL);
        int lastAlive = 0;
        int remaining = size;
        int cur_holder = k;

        for(int i=1; i<=size; i++){
                alive[i] = ALIVE;
        }
        
        while(remaining > 1){
        	int victim = FindNextAlive(alive, cur_holder, size);
        	alive[victim] = DEAD;
        	remaining--;
        	if(remaining==1) break;
        	cur_holder = FindNextAlive(alive, victim, size);
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

int LastSoldierN(int size, int k){


}

/*********************************Exercise 3**************************************/
void PrintSizeofDataTypes(){
    printf("Now int types:\n");
    printf("Size of int:            %ld bytes\n", sizeof(int));
    printf("Size of unsigned int:   %ld bytes\n", sizeof(unsigned int));
    printf("Size of short int:      %ld bytes\n", sizeof(short int));
    printf("Size of unsigned short: %ld bytes\n", sizeof(unsigned short));
    printf("Size of long int:       %ld bytes\n", sizeof(long int));
    printf("Size of unsigned long:  %ld bytes\n", sizeof(unsigned long));
    printf("Size of long long int:  %ld bytes\n", sizeof(long long int));

    printf("\n\nNow floating point types:\n");
    printf("Size of float:          %ld bytes\n", sizeof(float));
    printf("Size of double:         %ld bytes\n", sizeof(double));
    printf("Size of long double:    %ld bytes\n", sizeof(long double));


    printf("\n\nNow char types:\n");
    printf("Size of char:           %ld byte\n", sizeof(char));
    printf("Size of signed char:    %ld byte\n", sizeof(signed char));
    printf("Size of unsigned char:  %ld byte\n", sizeof(unsigned char));
    
    printf("\n\nNow NULL type:\n");
    printf("Size of void*:          %ld bytes\n", sizeof(void*));
}

/*********************************Exercise 4**************************************/
const char *delim = "=";
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

int SetLowEnviron(char* env, char **lowEnviron){
	char *token = strtok(env,delim);
	int len = strlen(token);
	*lowEnviron=malloc(len+1);
	if(*lowEnviron==NULL){
		perror("Failed to allocate string memory");
		return 1;
	}
	for(int j=0; j<len; j++){
		(*lowEnviron)[j] = tolower((unsigned char)token[j]);
	}
	(*lowEnviron)[len] = '\0';
	return 0;
}

static void FreeEnvMem(char **env, int size){
	for(int j=0; j<size; j++) free(env[j]);
        free(env);
}

int UpperToLowerEnviron(){
	int i=0, count=0, allo_error=0;
	while(environ[count]!=NULL) count++;
        char **low_environ = GetBuffer();
        if(low_environ == NULL) return 1;
        for(i=0; i < count; i++){
        	allo_error = SetLowEnviron(environ[i], &low_environ[i]);
        	if(allo_error==1){
        		FreeEnvMem(low_environ, i);
        		return 1;
        	}
        }
        low_environ[count] = NULL;
        printf("Lowercase Enviroment Variables:\n");
        for(int j=0; j<count; j++) printf("%s\n", low_environ[j]);
        FreeEnvMem(low_environ, count);
        return 0;
}



