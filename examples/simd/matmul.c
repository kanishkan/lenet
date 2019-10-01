#ifndef SIZE
#define SIZE 64
#endif

#ifndef VEC_WIDTH
#define VEC_WIDTH 2
#endif

#ifndef DATA_TYPE
#define DATA_TYPE int
#endif

#define VEC_COUNT (SIZE/VEC_WIDTH)

typedef DATA_TYPE scalar_t;
typedef scalar_t vector_t __attribute__((__ext_vector_type__(VEC_WIDTH)));

void matmul(vector_t* restrict A, scalar_t* restrict B,
            vector_t* restrict result) {
    for (unsigned y = 0; y < SIZE; y += 1) {
        for (unsigned k = 0; k < VEC_COUNT; k += 1) {
            result[k + VEC_COUNT*y] = 0;
            for (unsigned x = 0; x < SIZE; x += 1) {
                result[k + VEC_COUNT*y] += A[k + VEC_COUNT*x] * B[x + SIZE*y];
            }
        }
    }
}

int main() {
    // Constant pointers so that RTL simulation is easier
    volatile int* signal = (int*)(4*SIZE*SIZE-4);
    vector_t* op0 = (vector_t*)(4*SIZE*SIZE);
    scalar_t* op1 = (scalar_t*)(4*SIZE*SIZE*2);
    vector_t* res = (vector_t*)(4*SIZE*SIZE*3);

    matmul(op0, op1, res);
    *signal = -1;
    return 0;
}