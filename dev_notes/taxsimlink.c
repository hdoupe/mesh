#include <stdio.h>

extern void runmodel(char [], int);

int main(){
    char fname[] = "data.txt";
    runmodel(fname, sizeof(fname)/sizeof(fname[0]));
    return 0;
}
