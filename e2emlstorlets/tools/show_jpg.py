import sys
from matplotlib import pyplot as plt
import numpy as np
import cv2

def main(args):
    img_str = open(args[0],'r').read()
    img_nparr = np.fromstring(img_str, np.uint8)
    mat=cv2.imdecode(img_nparr, cv2.IMREAD_GRAYSCALE)
    plt.imshow(mat)
    plt.show()

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
~                                     
