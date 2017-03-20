import sys
import cv2
import json
import boto3
import pickle
import numpy as np
from e2emlstorlets.video_recognize_face.video_recognize_face import recognize_face, id_to_name_dict 


def main_loop(cap, capo, model, id_to_name):
    while(True):
        ret, frame = cap.read()
        out_image = frame

        # Calculate output frame
        if ret==True:
            name = recognize_face(frame, model, id_to_name)
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(out_image, name, (20, 100), font, 1, (200,255,155) )
            capo.write(out_image)
        else:
            print('No more frames. Exiting\n')
            break


def tag_movie_face(input_movie_path, input_model_path, id_to_name):
    model = None
    with open(input_model_path, 'r') as fmodel:
        model = pickle.load(fmodel)
    cap = cv2.VideoCapture(input_movie_path, cv2.CAP_FFMPEG)
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    fps=int(fps)
    width=int(width)
    height=int(height)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    capo = cv2.VideoWriter()
    capo.open('/tmp/tagged_movie.avi', fourcc, fps, (width,height))
    try:
        main_loop(cap, capo, model, id_to_name)
    except Exception as e:
        print('main_loop exception %s\n' % str(e))
        raise
    finally:
        cap.release()
        capo.release()


def get_tag_and_upload():
    client = boto3.client('s3')

    print('Downloading swapped movie from S3')
    res = client.get_object(Bucket='e2emlstorlets-video',
                            Key='eran_swapped_mov.avi')
    with open('/tmp/source_swapped_movie.avi','w') as f:
        while(True):
            buf = res['Body'].read(1024)
            if buf:
                f.write(buf)
            else:
                print('Swapped movie download Done.')
                break

    print('Downloading model')
    res = client.get_object(Bucket='e2emlstorlets-trained',
                            Key='model')
    name_to_id = json.loads(res['Metadata']['name_to_id'])
    id_to_name = id_to_name_dict(name_to_id)
    with open('/tmp/model','w') as f:
        while(True):
            buf = res['Body'].read(1024)
            if buf:
                f.write(buf)
            else:
                print('Model download Done.')
                break

    print('Tagging face')
    tag_movie_face('/tmp/source_swapped_movie.avi', '/tmp/model', id_to_name)

    print('Uploading Result')
    with open('/tmp/tagged_movie.avi','r') as f:
        client.put_object(Body=f,
                          Bucket='e2emlstorlets-video',
                          Key='eran_tagged_mov.avi')


def main():
    get_tag_and_upload()

if __name__ == "__main__":
    sys.exit(main())
