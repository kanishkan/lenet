import numpy as np
from imageio import imread

img_name = "test_data/img0.png"
weights_name = "weights.npy"

img = imread(img_name)
weights = np.load(weights_name, allow_pickle=True)


print("writing input image into weights.h ...")

f = open('weights.h', 'w')
img = img.flatten()
f.write("static char img[] = {")
for i in range(len(img)):
    if (i != 0):
        f.write(",")
    if(i%32 == 0):
        f.write("\n")
    f.write("%4d" % (img[i]))
    
f.write("};\n\n")

    
    
print("writing LeNet weights into weights.h ...")

for i, w in enumerate(weights):
    f.write("static const char w%d[] = {" % (i))
    w = w.flatten()
    for k in range(len(w)):
        if (k != 0):
            f.write(",")
        if(k%32 == 0):
            f.write("\n")
        f.write("%4d" % (w[k]))
        
    f.write("};\n\n")
        
f.close()
