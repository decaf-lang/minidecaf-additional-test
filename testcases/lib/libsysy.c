#include <stdarg.h>
#include <stdio.h>
#include <sys/time.h>

int getint() {
  int t;
  scanf("%d", &t);
  return t;
}

int getch() {
  char c;
  scanf("%c", &c);
  return (int)c;
}

int getarray(int a[]) {
  int n;
  scanf("%d", &n);
  for (int i = 0; i < n; i++)
    scanf("%d", &a[i]);
  return n;
}

int putint(int a) {
  printf("%d", a);
  return 0;
}
int putch(int a) {
  printf("%c", a);
  return 0;
}

int putarray(int n, int a[]) {
  printf("%d:", n);
  for (int i = 0; i < n; i++)
    printf(" %d", a[i]);
  printf("\n");
  return 0;
}
