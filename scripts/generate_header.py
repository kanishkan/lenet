#!/usr/bin/python3
import sys, getopt
import numpy as np
from imageio import imread

# TODO:
#   1. Helper function
#   2. Update Readme file in github

# Weights of the LeNet in numpy format
weights_name = "weights.npy"

# Read weights
nw_weights = np.load(weights_name, allow_pickle=True)

def writeData(f, img):
    img = img.flatten()
    f.write("static char img[%d] = {" %(len(img)))

    # Write as 1D array (sequentially)
    for i in range(len(img)):
        if (i != 0):
            f.write(",")
        if(i%32 == 0):
            f.write("\n")
        f.write("%4d" % (img[i]))

    f.write("};\n\n")

def writeWeights(f, weights = nw_weights):
    print("writing LeNet weights into weights.h ...")

    # For each layer
    for i, w in enumerate(weights):
        w = w.flatten() # Convert to 1D
        f.write("static const char w%d[%d] = {" % (i, len(w)))

        # Write as 1D in sequential order
        for k in range(len(w)):
            if (k != 0):
                f.write(",")
            if(k%32 == 0):
                f.write("\n")
            f.write("%4d" % (w[k]))

        f.write("};\n\n")

# main function
def main(img_name):
    # Create header file
    f = open('weights.h', 'w')
    image = imread(img_name)

    print("writing input image (%s) into weights.h ..." % (img_name))
    writeData(f, image)
    writeWeights(f)
    f.close()

# Entry point
if __name__ == '__main__':
    n_args = len(sys.argv)
    if (n_args != 2):
        print("usage: generate_header.py <input_img.png>")
    else:
        # Read input image
        img_name = sys.argv[1]
        main(img_name)
