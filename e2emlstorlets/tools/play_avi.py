import sys
import os
import cv2

def main(args):
    print args[0]
    cap = cv2.VideoCapture(args[0], cv2.CAP_FFMPEG)
    print(cap.isOpened())

    while(True):
        ret, frame = cap.read()

        # Display the resulting frame
        if ret==True:
            cv2.imshow('frame',frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            break
    cap.release()

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
