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
import random
import numpy as np
import sklearn.neural_network as snn

from ast import literal_eval


class TrainModel(object):
    def __init__(self, logger):
        self.logger = logger

    def parse_params(self, params):
        hidden_layer_sizes = params.get('hidden_layer_sizes','(100, 20, 8)')
        self.hidden_layer_sizes = literal_eval(hidden_layer_sizes)
        self.logger.debug('hidden_layer_sizes: %s %s\n' % (type(self.hidden_layer_sizes), self.hidden_layer_sizes))
        self.activation = params.get('activation', 'logistic')
        self.logger.debug('activation: %s %s\n' % (type(self.activation), self.activation))
        self.solver = params.get('solver', 'lbfgs')
        self.logger.debug('solver: %s %s\n' % (type(self.solver), self.solver))
        self.max_iter = int(params.get('max_iter', '2000'))
        self.logger.debug('max_iter: %s %s\n' % (type(self.max_iter), self.max_iter))
        self.alpha = float(params.get('alpha', '4e-8'))
        self.logger.debug('alpha: %s %s\n' % (type(self.alpha), self.alpha))
        self.tol = float(params.get('tol', '1e-9'))
        self.logger.debug('tol: %s %s\n' % (type(self.tol), self.tol))
        random_state = params.get('random_state', '')
        if random_state:
            self.random_state = int(random_state)
        else:
            self.random_state = None
        self.logger.debug('random_state: %s %s\n' % (type(self.random_state), self.random_state))

    def __call__(self, in_files, out_files, params):
        self.parse_params(params)
        metadata = {}
        out_files[0].set_metadata(metadata)

        i = 0
        num_files = len(in_files)
        X = np.ndarray(shape=(num_files,50*55), dtype=np.int32)
        y = np.ndarray(shape=(num_files,), dtype='|S6')

        random.shuffle(in_files)
        for input_file in in_files:
            md = input_file.get_metadata()
            name = md['Name']
            filename = md['Filename']

            img_str = ''
            while True:
                buf = input_file.read(1024)
                if not buf:
                    break
                img_str += buf   
            input_file.close()
            self.logger.debug('%s\n' % hash(img_str))
            img_nparray = np.fromstring(img_str, np.uint8)
            image_mat = cv2.imdecode(img_nparray, cv2.IMREAD_GRAYSCALE)
            image_array = np.asarray(image_mat[:,:])
            image_vec = image_array.reshape(1,2750)
            X[i,:] = image_vec
            y[i] = name
            i=i+1

        self.logger.debug('Done reading data\n')
    
        classifier = snn.MLPClassifier(
            hidden_layer_sizes=self.hidden_layer_sizes,
            activation=self.activation,
            solver=self.solver,
            max_iter=self.max_iter,
            alpha=self.alpha,
            tol=self.tol,
            random_state=None if self.random_state is None else self.random_state)
#        classifier = snn.MLPClassifier(
#            hidden_layer_sizes=(100, 20, 8),
#            activation='logistic',
#            solver='lbfgs',
#            max_iter=2000,
#            alpha=0.00000004,
#            tol=1e-9,
#            random_state=None)
        classifier.fit(X,y)
        self.logger.debug('Done Training\n')
        self.logger.debug('Classifier paramters used: %s\n' % classifier)
        self.logger.debug('score is %s\n' % classifier.score(X,y))
        self.logger.debug('classes are %s\n' % classifier.classes_)

        sclassifier = pickle.dumps(classifier)
        out_files[0].write(sclassifier)
        out_files[0].close()
