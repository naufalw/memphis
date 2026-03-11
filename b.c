#include <stdlib.h>

typedef struct {
  char letter; /* 1 byte  + 3 bytes padding */
  int age;     /* 4 bytes */
  char flag;   /* 1 byte  + 3 bytes padding */
  float score; /* 4 bytes */
} Padded;

int main() {

  int counter = 42;
  int *p_counter = &counter;
  char grade = 'A';
  float pi = 3.14f;
  char greeting[16] = "Hello, memviz!";

  int scores[5] = {95, 80, 73, 61, 100};

  Padded s = {.letter = 'A', .age = 25, .flag = 1, .score = 9.5f};
  int *heap_array = malloc(5 * sizeof(int));
  for (int i = 0; i < 5; i++)
    heap_array[i] = (i + 1) * 11; /* 11,22,33,44,55 */

  free(heap_array);
  return 0;
}
