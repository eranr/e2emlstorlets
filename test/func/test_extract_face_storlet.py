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
import unittest

from swiftclient import client
from e2emlstorlets.tools.swift_access import parse_config,\
    get_auth, put_local_file, deploy_storlet


class TestExtractFaceStorlet(unittest.TestCase):

    def setUp(self):
        self.container_name = str(uuid.uuid4())
        conf = parse_config('access.cfg')
        self.url, self.token = get_auth(conf)

        deploy_storlet(conf, 'e2emlstorlets/extract_face/extract_face.py', 'extract_face.ExtractFace')
        client.put_container(self.url, self.token, self.container_name)
        put_local_file(self.url, self.token, self.container_name,
                       os.path.join(conf['repo_dir'], 'test/data'), 'eran.jpg')

    def tearDown(self):
        client.delete_object(self.url, self.token,
                             self.container_name,
                             'eran.jpg')
        client.delete_object(self.url, self.token,
                             self.container_name,
                             'small_eran.jpeg')
        client.delete_container(self.url, self.token, self.container_name)

    def invoke_storlet(self, src_container, src_obj, dst_path, name):
        headers = {'X-Run-Storlet': 'extract_face.py',
                   'X-Storlet-Parameter-1': 'name:%s' % name}

        response_dict = {}
        client.copy_object(
            self.url, self.token,
            src_container, src_obj,
            destination=dst_path,
            headers=headers,
            response_dict=response_dict)

        self.assertTrue(response_dict['status']==201)


    def test_extract_face(self):
        self.invoke_storlet(self.container_name, 'eran.jpg',
                            os.path.join(self.container_name,'small_eran.jpeg'),
                                         'eran')
        headers, body = client.get_object(self.url, self.token,
                                          self.container_name,'small_eran.jpeg')

        self.assertTrue('x-object-meta-rect' in headers)
        self.assertTrue(headers['x-object-meta-rect']=='[498 119 621 242]')
