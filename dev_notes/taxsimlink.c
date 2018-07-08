#include <stdio.h>

extern void runmodel(char [], int);

int main(){
    char fname[] = "data.txt";
    int fnamesize = sizeof(fname)/sizeof(fname[0]);
    runmodel(fname, fnamesize);
    return 0;
}
