#define _DEBUG

#ifdef _DEBUG
#include <stdio.h>
#endif /* _DEBUG */
 
#include "weights.h"


void convolution2d(char* out_layer, char* in_layer, const char* kernel, int in_size, int kernel_size, int in_features, int out_features, int relu_en)
{
	int f, k, row, col, i, j;
	int acc;
	int in_size2 = in_size * in_size;
	int kernel_size2 = kernel_size * kernel_size;
	int kernel_size3 = kernel_size2 * in_features;
	int out_idx = 0;

	for (f = 0; f < out_features; f++) {
		for (row = 0; row < in_size - kernel_size + 1; row++) {
			for (col = 0; col < in_size - kernel_size + 1; col++) {
				acc = 0;
				for (k = 0; k < in_features; k++) {
					for (i = 0; i < kernel_size; i++) {
						for (j = 0; j < kernel_size; j++) {
							acc += in_layer[k*in_size2 + (row+i)*in_size + (col+j)] * kernel[f*kernel_size3 + k*kernel_size2 + i*kernel_size + j];
						}
					}
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

void fullyconnected(char* out_layer, char* in_layer, const char* kernel, int in_features, int out_features, int relu_en)
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

int main()
{
	int i;

	char layer1[5000];
	char layer2[5000];
	char net_out[10];

	convolution2d(layer1, img, w0, 32, 5, 1, 6, 1);
	pooling2d(layer2, layer1, 28, 6);

	convolution2d(layer1, layer2, w1, 14, 5, 6, 16, 1);
	pooling2d(layer2, layer1, 10, 16);

	fullyconnected(layer1, layer2, w2, 400, 120, 1);
	fullyconnected(layer2, layer1, w3, 120, 84, 1);
	fullyconnected(net_out, layer2, w4, 84, 10, 0);

	predicted_number = argmax(net_out, 10);

#ifdef _DEBUG
	printf("Outputs of the last layer:\n");
	for (i = 0; i < 10; i++) {
		printf("%d:%4d\n", i, net_out[i]);
	}
	printf("\nPredicted number is %d\n\n", predicted_number);
#endif /* _DEBUG */
	
	return 0;
}
