import sys
import numpy as np
import cv2
from matplotlib import pyplot as plt

def show_image(img_str):
    img_nparr = np.fromstring(img_str, np.uint8)
    mat=cv2.imdecode(img_nparr, cv2.IMREAD_COLOR)
    plt.imshow(mat)
    plt.show()

def main(args):
    img_str = open(args[0],'r').read()
    show_image(img_str)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
