#ifdef HOST_DEBUG
#include <stdio.h>
#else
#include "tceops.h"
#endif /* HOST_DEBUG */

#include "weights.h"

#ifdef SIMD // Create SIMD Datatype
typedef char vector_t __attribute__((__ext_vector_type__(4)));
#endif

void convolution2d(char* out_layer, char* in_layer, const char* kernel,
        int in_size, int kernel_size, int in_features, int out_features, int relu_en)
{
    int f, k, row, col, i, j;
    int acc;
    int in_size2 = in_size * in_size;
    int kernel_size2 = kernel_size * kernel_size;
    int kernel_size3 = kernel_size2 * in_features;
    int out_idx = 0;

    for (f = 0; f < out_features; f++) {
        for (row = 0; row < in_size - kernel_size + 1; row++) {
            #pragma clang loop unroll(disable)
            for (col = 0; col < in_size - kernel_size + 1; col++) {
                acc = 0;
#if SIMD        // Define vector acc
                volatile vector_t acc_vect = {0,0,0,0};
#endif
                for (k = 0; k < in_features; k++) {
                    #pragma clang loop unroll(disable)
                    for (i = 0; i < kernel_size; i++) {

#ifndef SIMD            // Sclar version
                        #pragma clang loop unroll(disable)
                        for (j = 0; j < kernel_size; j++) {
                            acc += in_layer[k*in_size2 + (row+i)*in_size + (col+j)] *
                                    kernel[f*kernel_size3 + k*kernel_size2 + i*kernel_size + j];
                        }
#else                   // If SIMD is enabled
                        vector_t *in_vect_ptr = (vector_t *) &in_layer[k*in_size2 + (row+i)*in_size + (col)];
                        vector_t *w_vect_ptr = (vector_t *) &kernel[f*kernel_size3 + k*kernel_size2 + i*kernel_size];
                        // Load vector and do vector mac
                        vector_t w_data, in_data;
                        _TCEAS_LD8X4("data", w_vect_ptr, w_data);
                        _TCEAS_LD8X4("data", in_vect_ptr, in_data);
                        _TCE_MAC8X4(acc_vect, in_data, w_data, acc_vect);

                        // Border case
                        acc += in_layer[k*in_size2 + (row+i)*in_size + (col+kernel_size-1)] *
                            kernel[f*kernel_size3 + k*kernel_size2 + i*kernel_size + kernel_size-1];
#endif
                    }
                }

#ifdef SIMD            // If we use SIMD, extract individual elemnts and add them
                int tmp;
                for (int lane=0; lane<4; lane++) {
                    _TCE_EXTRACTELEM8X4(acc_vect, i, tmp);
                    acc += tmp;
                }
#endif
                acc = acc >> 9;
                if (acc > 127) {
                    acc = 127;
                }
                else if (acc < 0 && relu_en != 0) {
                    acc = 0;
                }
                else if (acc < -128) {
                    acc = -128;
                }

                out_layer[out_idx++] = acc;
            }
        }
    }
}

void pooling2d(char* out_layer, char* in_layer, int in_size, int features) {
    int f, row, col;
    char max;
    int in_size2 = in_size * in_size;
    int out_idx = 0;

    for (f = 0; f < features; f++) {
        for (row = 0; row < in_size; row+=2) {
            for (col = 0; col < in_size; col+=2) {
                max = in_layer[f*in_size2 + row * in_size + col];
                if (in_layer[f*in_size2 + (row)*in_size + (col+1)] > max)
                    max = in_layer[f*in_size2 + (row)*in_size + (col+1)];
                if (in_layer[f*in_size2 + (row+1)*in_size + (col)] > max)
                    max = in_layer[f*in_size2 + (row+1)*in_size + (col)];
                if (in_layer[f*in_size2 + (row+1)*in_size + (col+1)] > max)
                    max = in_layer[f*in_size2 + (row+1)*in_size + (col+1)];
                out_layer[out_idx++] = max;
            }
        }
    }

}

void fullyconnected(char* out_layer, char* in_layer, const char* kernel,
        int in_features, int out_features, int relu_en)
{
    int f, k, row, col, i, j;
    int acc;

    for (f = 0; f < out_features; f++) {
        acc = 0;
        for (k = 0; k < in_features; k++) {
            acc += in_layer[k] * kernel[f*in_features + k];
        }
        acc = acc >> 9;
        if (acc > 127) {
            acc = 127;
        }
        else if (acc < 0 && relu_en != 0) {
            acc = 0;
        }
        else if (acc < -128) {
            acc = -128;
        }

        out_layer[f] = acc;
    }
}

int argmax(char* numbers, int len)
{
    int i;
    char max = -128;
    int argm = 0;

    for (i = 0; i < len; i++) {
        if (numbers[i] > max) {
            max = numbers[i];
            argm = i;
        }
    }

    return argm;
}

volatile int predicted_number;
volatile unsigned int ecc, lcc;
char layer1[5000];
char layer2[5000];
char net_out[10];

int main()
{
    int i;

    convolution2d(layer1, img, w0, 32, 5, 1, 6, 1);
    pooling2d(layer2, layer1, 28, 6);

    convolution2d(layer1, layer2, w1, 14, 5, 6, 16, 1);
    pooling2d(layer2, layer1, 10, 16);

    fullyconnected(layer1, layer2, w2, 400, 120, 1);
    fullyconnected(layer2, layer1, w3, 120, 84, 1);
    fullyconnected(net_out, layer2, w4, 84, 10, 0);

    predicted_number = argmax(net_out, 10);

#ifdef HOST_DEBUG
    printf("Outputs of the last layer:\n");
    for (i = 0; i < 10; i++) {
        printf("%d:%4d\n", i, net_out[i]);
    }
    printf("\nPredicted number is %d\n\n", predicted_number);
#else
    // The ECC and LCC instruction returns cycle count information
    // Useful to profile the design on FPGA (enable them for FPGA flow)
    // unsigned int tmp;
    // _TCE_ECC(tmp, ecc);
    // _TCE_LCC(tmp, lcc);
#endif /* HOST_DEBUG */

    return 0;
}
