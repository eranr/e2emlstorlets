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
import json
import pickle
import numpy as np
import sklearn.neural_network as snn

class TrainModel(object):
    def __init__(self, logger):
        self.logger = logger

    def __call__(self, in_files, out_files, params):
        metadata = {}
        out_files[0].set_metadata(metadata)

        i = 0
        num_files = len(in_files)
        X = np.ndarray(shape=(num_files,50*55), dtype=np.int32)
        y = np.ndarray(shape=(num_files,), dtype='|S6')

        for input_file in in_files:
            md = input_file.get_metadata()
            self.logger.debug('md is %s\n' % md)
            name = md['Name']

            img_str = ''
            while True:
                buf = input_file.read(1024)
                if not buf:
                    break
                img_str += buf   
            input_file.close()
            self.logger.debug('Recieved %d bytes\n' % len(img_str))
            img_nparray = np.fromstring(img_str, np.uint8)
            image_mat = cv2.imdecode(img_nparray, cv2.IMREAD_GRAYSCALE)
            image_array = np.asarray(image_mat[:,:])
            image_vec = image_array.reshape(1,2750)
            X[i,:] = image_vec
            y[i] = name
            i=i+1
            self.logger.debug('Done with %s\n' % name)

        self.logger.debug('Done reading data\n')
    
        classifier = snn.MLPClassifier(
            hidden_layer_sizes=(100,50,25,10),
            activation='logistic',
            solver='lbfgs',
            max_iter=2000,
            alpha=0.000001,
            tol=1e-7,
            random_state=1)
        classifier.fit(X,y)
        self.logger.debug('Done Training\n')

        sclassifier = pickle.dumps(classifier)
        out_files[0].write(sclassifier)
        out_files[0].close()
