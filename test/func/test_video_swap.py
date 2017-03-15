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


class TestSwapFace(unittest.TestCase):

    def setUp(self):
        self.container_name = str(uuid.uuid4())
        conf = parse_config('access.cfg')
        self.url, self.token = get_auth(conf)
        self.repo_dir=conf['repo_dir']

        deploy_storlet(conf, 'e2emlstorlets/video_swap_face/video_swap_face.py',
                       'video_swap_face.MovieSwapFace')
        client.put_container(self.url, self.token, self.container_name)
        put_local_file(self.url, self.token, self.container_name,
                       os.path.join(conf['repo_dir'], 'test/data'),
                       'eran.jpg')
        put_local_file(self.url, self.token, self.container_name,
                       os.path.join(conf['repo_dir'], 'test/data'),
                       'eran_mov.avi')

    def tearDown(self):
        client.delete_object(self.url, self.token,
                             self.container_name,
                             'eran.jpg')
        client.delete_object(self.url, self.token,
                             self.container_name,
                             'eran_mov.avi')
        client.delete_object(self.url, self.token,
                             self.container_name,
                             'eran_swapped_mov.avi')
        client.delete_container(self.url, self.token, self.container_name)

    def invoke_storlet(self):
        headers = {'X-Run-Storlet': 'video_swap_face.py'}
        source_obj1 = 'eran_mov.avi'
        source_obj2 = os.path.join('/' + self.container_name,
                                   'eran.jpg')
        headers['X-Storlet-Extra-Resources'] = source_obj2
        dst_path = os.path.join(self.container_name, 'eran_swapped_mov.avi')

        response_dict = {}
        client.copy_object(
            self.url, self.token,
            self.container_name, source_obj1,
            destination=dst_path,
            headers=headers,
            response_dict=response_dict)

        self.assertTrue(response_dict['status']==201)

    def test_swap_face(self):
        self.invoke_storlet()
        headers, body = client.get_object(self.url, self.token,
                                          self.container_name, 'eran_swapped_mov.avi')
