# Copyright (c) 2016 Satya Mallic (learnopencv)
# Copyright (c) 2015 Matthew Earl

import os
import sys
import numpy as np
import cv2
import json
import pickle
import threading
from contextlib import contextmanager


def crop(img, rect):
    h = rect[3]-rect[1]
    w = rect[2]-rect[0]
    x = rect[0]
    y = rect[1]
    # account for forehead part
    hm = int(0.1 * h)
    if y < hm:
        h = h + (hm - y)
        hm = y
    return img[y-hm:y+h, x:x+w]


def recognize_face(frame, model):
    cascade = cv2.CascadeClassifier("/usr/local/share/OpenCV/haarcascades/haarcascade_frontalface_alt2.xml")
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rects = cascade.detectMultiScale(gray_frame)
    if len(rects) == 0:
        return 'None'
    rects[:, 2:] += rects[:, :2]
    face = crop(gray_frame, rects[0])
    small_face = cv2.resize(face, (50,55))
    small_face_array = np.asarray(small_face[:,:])
    small_face_vec = small_face_array.reshape(1,2750)
    name = model.predict(small_face_vec)[0]
    return name


@contextmanager
def avi_fifo(name, logger):
    try:
        os.mkfifo(name, 0666)
    except OSError as e:
        if e.errno == 17:
            os.unlink(name)
            os.mkfifo(name, 0666)
        else:
            logger.debug('mkfifo exception %s' % str(e))

    try:
        yield
    finally:
        os.unlink(name)

class fifo_worker(threading.Thread):
    def __init__(self, output, fifo_name, logger):
        threading.Thread.__init__(self)
        self.output = output
        self.fifo_name = fifo_name
        self.logger = logger

    def run(self):
        fd = os.open(self.fifo_name, os.O_RDONLY)
        self.logger.debug('fifo %d is opened for reading\n' % fd)

        while(True):
            try:
                chunk = os.read(fd, 1024*64)
                if len(chunk)>0:
                    self.output.write(chunk)
                else:
                    self.logger.debug('empty chunk\n')
                    break
            except OSError as e:
                self.logger.debug('worker exception\n' % str(e))
                break

        os.close(fd)
        self.logger.debug('fifo worker exits\n')

def main_loop(cap, capo, model, logger):
    hist = {'bibi': 0,'merkel': 0,'obama': 0,'trump': 0, 'None': 0}
    while(True):
        ret, frame = cap.read()
        out_image = frame

        # Calculate output frame
        if ret==True:
            name = recognize_face(frame, model)
            hist[name] += 1
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(out_image, name, (20, 100), font, 1, (200,255,155) )
            capo.write(out_image)
        else:
            logger.debug('No more frames. Exiting\n')
            break

    logger.debug('Stats: %s\n' % hist)

class MovieRecognizeFace(object):
    def __init__(self, logger):
        self.logger = logger

    def __call__(self, in_files, out_files, params):
        """
        in_files[0] is assumed to be the movie
        in_files[1] is assumed to be the trained model
        """
        out_files[0].set_metadata(in_files[0].get_metadata())
        movie_file = in_files[0]
        movie_fd = movie_file.fileno()
        model_file = in_files[1]

        classifier_buf = ''
        while True:
            buf = model_file.read(1024)
            if not buf:
                break
            classifier_buf += buf   
        self.logger.debug('model read\n')
        model = pickle.loads(classifier_buf)
        model_file.close()
        self.logger.debug('model decoded\n')
        self.logger.debug('model=%s\n' % model)

        fifo_name = '/tmp/fifo_%s.avi' % str(os.getpid())
        with avi_fifo(fifo_name, self.logger):
            worker = fifo_worker(out_files[0], fifo_name,
                                 self.logger)
            worker.start()

            cap = cv2.VideoCapture('pipe:%d' % movie_fd, cv2.CAP_FFMPEG)
            self.logger.debug('movie reader opened\n')
            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            fps = cap.get(cv2.CAP_PROP_FPS)
            fps=int(fps)
            width=int(width)
            height=int(height)
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            capo = cv2.VideoWriter()
            capo.open(fifo_name, fourcc, fps, (width,height))
            self.logger.debug('movie writer opened\n')

            try:
                main_loop(cap, capo, model, self.logger)
            except Exception as e:
                self.logger.debug('main_loop exception %s\n' % str(e))
                raise
            finally:
                capo.release()
                self.logger.debug('Awaiting worker thread to finish\n')
                worker.join()
                self.logger.debug('Worker thread finished\n')

        cap.release()
        movie_file.close()
        self.logger.debug('Done.')
