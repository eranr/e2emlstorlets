# Copyright (c) 2017 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import cv2
import numpy as np

def detect(im):
    mat=cv2.imdecode(im, cv2.IMREAD_GRAYSCALE)
    cascade = cv2.CascadeClassifier("/usr/local/share/OpenCV/haarcascades/haarcascade_frontalface_alt2.xml")
    rects = cascade.detectMultiScale(mat)

    if len(rects) == 0:
        return [], mat
    rects[:, 2:] += rects[:, :2]
    rect = rects[0]
    return mat, rect

def crop(img, rect):
    h = rect[3]-rect[1]
    w = rect[2]-rect[0]
    x = rect[0]
    y = rect[1]
    # account for forehead part
    hm = 0.1 * h
    hm = int(hm)
    if y >= hm:
        cropped = img[y-hm:y+h, x:x+w]
    else:
        h = h + (hm - y)
        hm = y
        cropped = img[y-hm:y+h, x:x+w]
    return cropped


class ExtractFace(object):
    def __init__(self, logger):
        self.logger = logger
        
    def __call__(self, in_files, out_files, params):
        self.logger.debug('Returning metadata\n')
        metadata = in_files[0].get_metadata()
        metadata['name'] = params.get('name', '')

        self.logger.debug('Start to read object data\n')
        img_str = ''
        while True:
            buf = in_files[0].read(1024)
            if not buf:
                break
            img_str += buf

        self.logger.debug('Detecting face bounding rectangle\n')
        img_nparr = np.fromstring(img_str, np.uint8)
        mat, rect = detect(img_nparr)
        metadata['rect']=str(rect)
        out_files[0].set_metadata(metadata)
        face = crop(mat, rect)
        small_face = cv2.resize(face, (50,55))
        retval, small_face_buf = cv2.imencode('.jpg', small_face)
        out_files[0].write(small_face_buf)
        in_files[0].close()
        out_files[0].close()
        self.logger.debug('Done\n')
