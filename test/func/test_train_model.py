# Copyright (c) 2017 itsonlyme.name
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

import os
import uuid
import json
import pickle
import unittest
import sklearn.neural_network as snn

from swiftclient import client
from e2emlstorlets.tools.swift_access import parse_config,\
    get_auth, put_local_file, deploy_storlet


class TestTrainModel(unittest.TestCase):

    def setUp(self):
        self.container_name = str(uuid.uuid4())
        conf = parse_config('access.cfg')
        self.url, self.token = get_auth(conf)
        self.repo_dir=conf['repo_dir']

        deploy_storlet(conf, 'e2emlstorlets/train_model/train_model.py',
                       'train_model.TrainModel')
        client.put_container(self.url, self.token, self.container_name)
        headers = {'X-Object-Meta-Name': 'eran'}
        put_local_file(self.url, self.token, self.container_name,
                       os.path.join(conf['repo_dir'], 'test/data'),
                                    'small_eran.jpeg', headers=headers)
        client.copy_object(self.url, self.token, self.container_name,
                           'small_eran.jpeg',
                           '%s/small_eran_2.jpeg' % self.container_name)
        client.copy_object(self.url, self.token, self.container_name,
                           'small_eran.jpeg',
                           '%s/small_eran_3.jpeg'% self.container_name)

    def tearDown(self):
        client.delete_object(self.url, self.token,
                             self.container_name,
                             'small_eran.jpeg')
        client.delete_object(self.url, self.token,
                             self.container_name,
                             'small_eran_2.jpeg')
        client.delete_object(self.url, self.token,
                             self.container_name,
                             'small_eran_3.jpeg')
        client.delete_object(self.url, self.token,
                             self.container_name,
                             'model')
        client.delete_container(self.url, self.token, self.container_name)

    def invoke_storlet(self):
        name_to_id = {'eran': 1 }
        name_to_id_str = json.dumps(name_to_id)
        headers = {'X-Run-Storlet': 'train_model.py'}
        source_obj1 = 'small_eran.jpeg'
        source_obj2 = os.path.join('/' + self.container_name,
                                   'small_eran_2.jpeg')
        source_obj3 = os.path.join('/' + self.container_name,
                                   'small_eran_3.jpeg')
        headers['X-Storlet-Extra-Resources'] = '%s, %s' % (source_obj2, source_obj3)
        dst_path = os.path.join(self.container_name, 'model')

        response_dict = {}
        client.copy_object(
            self.url, self.token,
            self.container_name, source_obj1,
            destination=dst_path,
            headers=headers,
            response_dict=response_dict)

        self.assertTrue(response_dict['status']==201)

    def test_train_model(self):
        self.invoke_storlet()
        headers, body = client.get_object(self.url, self.token,
                                          self.container_name, 'model')
        regressor = pickle.loads(body)
