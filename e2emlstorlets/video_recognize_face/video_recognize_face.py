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
    return img[y:y+h, x:x+w]


def recognize_face(frame, model, id_to_name):
    cascade = cv2.CascadeClassifier("/usr/local/share/OpenCV/haarcascades/haarcascade_frontalface_alt.xml")
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rects = cascade.detectMultiScale(gray_frame)
    if len(rects) == 0:
        return [], mat
    rects[:, 2:] += rects[:, :2]
    face = crop(gray_frame, rects[0])
    small_face = cv2.resize(face, (30,30))
    small_face_array = np.asarray(small_face[:,:])
    small_face_vec = small_face_array.reshape(1,900)
    face_id = model.predict(small_face_vec)
    name = 'I do not know'
    try:
        name = id_to_name[round(face_id)]
    except KeyError:
        pass

    return name


def id_to_name_dict(name_to_id):
    id_to_name = dict()
    for k in name_to_id.keys():
        id_to_name[name_to_id[k]] = k

    return id_to_name

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

def main_loop(cap, capo, model, id_to_name, logger):
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
            logger.debug('No more frames. Exiting\n')
            break

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
        model_md = model_file.get_metadata()
        self.logger.debug('metadata type is %s' % str(type(model_md)))
        for k in model_md.keys():
            self.logger.debug('k=%s, v=%s\n' % (str(k), str(model_md[k])))
        name_to_id = json.loads(model_md['Name-To-Id'])
        id_to_name = id_to_name_dict(name_to_id)

        regressor_buf = ''
        while True:
            buf = model_file.read(1024)
            if not buf:
                break
            regressor_buf += buf   
        self.logger.debug('model read\n')
        model = pickle.loads(regressor_buf)
        model_file.close()
        self.logger.debug('model decoded\n')

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
                main_loop(cap, capo, model, id_to_name, self.logger)
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
