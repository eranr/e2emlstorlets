import sys
import os
import cv2


def play(filename):
    cap = cv2.VideoCapture(filename, cv2.CAP_FFMPEG)

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
    cv2.destroyAllWindows()

def main(args):
    print args[0]
    play(args[0])

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
