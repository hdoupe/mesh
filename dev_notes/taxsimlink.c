#include <stdio.h>

extern void runmodel(char [], int, char [], int);

int main(){
    char fname[] = "data.txt";
    int fnamesize = sizeof(fname)/sizeof(fname[0]);
    char arg[] = "full";
    int argsize = sizeof(arg)/sizeof(fname[0]);
    runmodel(fname, fnamesize, arg, argsize);
    return 0;
}
