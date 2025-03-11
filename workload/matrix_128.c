#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <sys/time.h>
#include <assert.h>
#include <stdint.h>

#define MAX_VALUE 1000
#define N_COLS 1000
#define N_ROWS 1000

#define uint128_t __int128

typedef struct matrix {
    uint128_t num_rows;
    uint128_t num_cols;
    uint128_t **data;
} matrix;

matrix *A;
matrix *B;
matrix *C;


void *mul_row_thread(void *arg) {
    int row_id = (int)arg;

    // will create C[row_id]:

    for (unsigned int i = 0; i < A->num_cols; i++) {
        for (unsigned int j = 0; j < B->num_rows; j++)
            C->data[row_id][j] += A->data[row_id][i] * B->data[i][j];
    }

    return NULL;

}


void print_matrix(matrix *m) {
    assert(m != NULL);

   for (unsigned int i = 0; i < m->num_rows; i++) {
        for (unsigned int j = 0; j < m->num_cols; j++) {
            printf("%*d ", 4, m->data[i][j]);
        }
        printf("\n");
    }
    printf("\n");
}


void init_matrix(matrix *m, int n_rows, int n_cols) {
    assert(n_rows>0);
    assert(n_cols>0);

    m->num_rows = n_rows;
    m->num_cols = n_cols;
    m->data = (uint128_t **)malloc(n_rows * sizeof(uint128_t *));
    if (!m->data) {
        fprintf(stderr, "failed to allocate space for matrix!\n");
    }

    for (unsigned int i = 0; i < n_rows; i++) {
        m->data[i] = malloc(n_cols * sizeof(uint128_t));
        if (!m->data[i]) {
            fprintf(stderr, "failed to allocate space for matrix!\n");
        }

        for (unsigned int j = 0; j < n_cols; j++) {
            // yes this is not completely uniformly random. But good enought.
            m->data[i][j] = (uint128_t)rand() % MAX_VALUE;
        }
    }
}


void zero_init_matrix(matrix *m, int n_rows, int n_cols) {
    assert(n_rows>0);
    assert(n_cols>0);

    m->num_rows = n_rows;
    m->num_cols = n_cols;
    m->data = (uint128_t **)malloc(n_rows * sizeof(uint128_t *));
    if (!m->data) {
        fprintf(stderr, "failed to allocate space for matrix!\n");
    }

    for (unsigned int i = 0; i < n_rows; i++) {
        m->data[i] = malloc(n_cols * sizeof(uint128_t));
        if (!m->data[i]) {
            fprintf(stderr, "failed to allocate space for matrix!\n");
        }

        for (unsigned int j = 0; j < n_cols; j++) {
            m->data[i][j] = (uint128_t)0;
        }
    }
}

void free_matrix(matrix *m) {
    assert(m != NULL);

    for (unsigned int i = 0; i < m->num_rows; i++) {
        free(m->data[i]);
    }

    free(m->data);

    m->data = NULL;
    m->num_rows = 0;
    m->num_cols = 0;
}


int main(int argc, char * argv[]) {
    srand(time(NULL));
    // allocate matrizes
    A = malloc(sizeof(struct matrix));
    if (!A) {
        fprintf(stderr, "failed to allocate space for matrix!\n");
    }

    B = malloc(sizeof(struct matrix));
    if (!B) {
        fprintf(stderr, "failed to allocate space for matrix!\n");
    }

    C = malloc(sizeof(struct matrix));
    if (!C) {
        fprintf(stderr, "failed to allocate space for matrix!\n");
    }

    init_matrix(A, N_ROWS, N_COLS);
    init_matrix(B, N_ROWS, N_COLS);
    zero_init_matrix(C, N_ROWS, N_COLS);

    pthread_t threads[N_ROWS];


    for (unsigned int i = 0; i < N_ROWS; i++) {
        if (pthread_create(&threads[i], NULL, mul_row_thread, (void *)i)) {
            fprintf(stderr, "failed to create threads!");
            return EXIT_FAILURE;
        }

    }

    for (unsigned int i = 0; i < N_ROWS; i++) {
        pthread_join(threads[i], NULL);
    }

    print_matrix(A);
    print_matrix(B);
    print_matrix(C);


}
