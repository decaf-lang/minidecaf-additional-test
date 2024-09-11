int getint();
int getch();
int getarray(int a[]);

int putint(int a);
int putch(int a);
int putarray(int n, int a[]);


int x;  

void mv(int n, int A[][2010], int b[], int res[]){
    int x, y;
    y = 0;
    x = 11;
    int i, j;

    i = 0;
    while(i < n){    
        res[i] = 0;        
        i = i + 1;
    }

    i = 0;
    j = 0;
    while (i < n){
        j = 0;
        while (j < n){
            if (A[i][j] == 0){
                x = x * b[i] + b[j];
                y = y - x;
            }else{
                res[i] = res[i] + A[i][j] * b[j];
            }
            j = j + 1;
        }
        i = i + 1;
    }    
}

int A[2010][2010];
int B[2010];
int C[2010];

int main(){
    int n = getint();
    int i, j;

    i = 0;

    while (i < n){
        j = 0;
        while (j < n){
            A[i][j] = getint();
            j = j + 1;
        }
        i = i + 1;
    }

    i = 0;
    while (i < n){
        B[i] = getint();
        i = i + 1;
    }


    i = 0;
    while (i < 50){
        mv(n, A, B, C);
        mv(n, A, C, B);
        i = i + 1;
    }

    putarray(n, C);
    return 0;
}