import sys
import os
import cv2

def main(args):

    fdi = os.open(args[0], os.O_RDONLY)
    cap = cv2.VideoCapture('pipe:%d' % fdi, cv2.CAP_FFMPEG)

    while(True):
        ret, frame = cap.read()

        # Display the resulting frame
        if ret==True:
            cv2.imshow('frame',frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            break
    os.close(fdi)
    cap.release()

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
