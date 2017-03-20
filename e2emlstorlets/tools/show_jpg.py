import sys
import numpy as np
import cv2

def show_image(img_str):
    img_nparr = np.fromstring(img_str, np.uint8)
    mat=cv2.imdecode(img_nparr, cv2.IMREAD_GRAYSCALE)
    cv2.imshow('frame', mat)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def main(args):
    img_str = open(args[0],'r').read()
    show_image(img_str)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
