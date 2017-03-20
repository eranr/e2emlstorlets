import sys
import cv2
import boto3
import numpy as np
from e2emlstorlets.video_swap_face.video_swap_face import swap_face 

def main_loop(cap, capo, face):
    while(True):
        ret, frame = cap.read()
        out_image = frame

        # Calculate output frame
        if ret==True:
            out_image = swap_face(frame, face)
            out_image = out_image.astype(np.uint8)
            capo.write(out_image)
        else:
            print('No more frames. Exiting\n')
            break

def swap_movie_face(input_movie_path, input_face_path):
    face_im = cv2.imread(input_face_path, cv2.IMREAD_COLOR)
    cap = cv2.VideoCapture(input_movie_path, cv2.CAP_FFMPEG)
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    fps=int(fps)
    width=int(width)
    height=int(height)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    capo = cv2.VideoWriter()
    capo.open('/tmp/swapped_movie.avi', fourcc, fps, (width,height))
    try:
        main_loop(cap, capo, face_im)
    except Exception as e:
        print('main_loop exception %s\n' % str(e))
        raise
    finally:
        cap.release()
        capo.release()

def get_swap_and_upload(face_object):
    client = boto3.client('s3')

    print('Downloading source movie from S3')
    res = client.get_object(Bucket='e2emlstorlets-video',
                            Key='eran_mov.avi')
    with open('/tmp/source_movie.avi','w') as f:
        while(True):
            buf = res['Body'].read(1024)
            if buf:
                f.write(buf)
            else:
                print('Download Done.')
                break

    print('Downloading face image %s' % face_object)
    res = client.get_object(Bucket='e2emlstorlets-test',
                            Key=face_object)
    with open('/tmp/source_face.jpeg','w') as f:
        f.write(res['Body'].read())

    print('Swapping face')
    swap_movie_face('/tmp/source_movie.avi', '/tmp/source_face.jpeg')

    print('Uploading Result')
    with open('/tmp/swapped_movie.avi','r') as f:
        client.put_object(Body=f,
                          Bucket='e2emlstorlets-video',
                          Key='eran_swapped_mov.avi')


def main(args):
    get_swap_and_upload(args[0])

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
