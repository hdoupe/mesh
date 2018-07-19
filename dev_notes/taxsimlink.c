#include <stdio.h>

extern void runmodel(char [], int, char [], int, char *, int);

int main(){
    char fname[] = "data.txt";
    int fnamesize = sizeof(fname)/sizeof(fname[0]);
    char arg[] = "full";
    int argsize = sizeof(arg)/sizeof(arg[0]);
    char *buffer;
    int buffersize = 20;
    buffer = (char*) malloc(sizeof(char) * buffersize);
    runmodel(fname, fnamesize, arg, argsize, buffer, buffersize);
    printf("got result: %s\n", buffer);
    return 0;
}
