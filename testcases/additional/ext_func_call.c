int putint(int a);
int putch(int a);
int putarray(int n, int a[]);

int main(){
    int a[10] = {1, 2, 3, 4, 5};
    putarray(10, a);
    putch(10);
    putint(10);
    putch(10);
    return 0;
}