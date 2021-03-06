# Copyright (c) 2015, 2016 OpenStack Foundation.
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


"""Implementation of magic funcs for interaction with the OpenStack Storlets.

This extension is desined to use os environment variables to set
authentication and storage target host. (for now)

"""
from __future__ import print_function

import os
import string
import cv2
from IPython.display import clear_output
from swiftclient.client import Connection
from play_avi import play
from show_jpg import show_image

from IPython.core import magic_arguments
# TODO(kota_): we may need some error handing in ipython shell so keep those
#              errors import as references.
# from IPython.core.alias import AliasError, Alias
from IPython.core.error import UsageError
from IPython.core.magic import Magics, magics_class, cell_magic, line_magic
from IPython.utils.py3compat import unicode_type


def get_swift_connection():
    # find api version
    for k in ('ST_AUTH_VERSION', 'OS_AUTH_VERSION', 'OS_IDENTITY_API_VERSION'):
        if k in os.environ:
            auth_version = os.environ[k]
            break
    else:
        auth_version = 1

    # cast from string to int
    auth_version = int(float(auth_version))

    if auth_version == 3:
        # keystone v3
        try:
            auth_url = os.environ['OS_AUTH_URL']
            auth_user = os.environ['OS_USERNAME']
            auth_password = os.environ['OS_PASSWORD']
            project_name = os.environ['OS_PROJECT_NAME']
        except KeyError:
            raise UsageError(
                "You need to set OS_AUTH_URL, OS_USERNAME, OS_PASSWORD and "
                "OS_PROJECT_NAME for Swift authentication")
        auth_os_options = {
            'user_domain_name': os.environ.get(
                'OS_USER_DOMAIN_NAME', 'Default'),
            'project_domain_name': os.environ.get(
                'OS_PROJECT_DOMAIN_NAME', 'Default'),
            'project_name': project_name
        }
        return Connection(auth_url, auth_user, auth_password,
                          os_options=auth_os_options,
                          auth_version='3')

    elif auth_version == 2:
        # keystone v2 (not implemented)
        raise NotImplementedError('keystone v2 is not supported')
    else:
        try:
            auth_url = os.environ['ST_AUTH']
            auth_user = os.environ['ST_USER']
            auth_password = os.environ['ST_KEY']
        except KeyError:
            raise UsageError(
                "You need to set ST_AUTH, ST_USER, ST_KEY for "
                "Swift authentication")
        return Connection(auth_url, auth_user, auth_password)


@magics_class
class StorletMagics(Magics):
    """Magics to interact with OpenStack Storlets
    """

    def _parse_input_path(self, path_arg):
        if not path_arg.startswith('path:'):
            raise UsageError(
                'swift object path must have the format: '
                '"path:/<container>/<object>"')
        try:
            src_container_obj = path_arg[len('path:'):]
            src_container, src_obj = src_container_obj.strip(
                '/').split('/', 1)
            return src_container, src_obj
        except ValueError:
            raise UsageError(
                'swift object path must have the format: '
                '"path:/<container>/<object>"')

    def _generate_params_headers(self, args):
        headers = {}
        if not args.i:
            return headers

        user_ns = self.shell.user_ns
        params = user_ns[args.i]

        i = 0
        for key in params:
            headers['X-Storlet-Parameter-%d' % i] =\
                '%s:%s' % (key, params[key])
            i = i + 1

        return headers

    @magic_arguments.magic_arguments()
    @magic_arguments.argument(
        'container_obj', type=unicode_type,
        help='container/object path to upload'
    )
    @cell_magic
    def uploadfile(self, line, cell):
        """Upload the contents of the cell to OpenStack Swift.
        """
        args = magic_arguments.parse_argstring(self.uploadfile, line)
        container, obj = args.container_obj.split('/', 1)
        conn = get_swift_connection()
        conn.put_object(container, obj, cell,
                        {'Content-Type': 'application/python'})

    @magic_arguments.magic_arguments()
    @magic_arguments.argument(
        'module_class', type=unicode_type,
        help='module and class name to upload'
    )
    @magic_arguments.argument(
        '-c', '--container', type=unicode_type, default='storlet',
        help='Storlet container name, "storlet" in default'
    )
    @magic_arguments.argument(
        '-d', '--dependencies', type=unicode_type, default='storlet',
        help='Storlet container name, "storlet" in default'
    )
    @magic_arguments.argument(
        '--with-invoke', action='store_true', default=False,
        help='An option to run storlet for testing. '
             'This requires --input option'
    )
    @magic_arguments.argument(
        '--input', type=unicode_type, default='',
        help='Specifiy input object path that must be of the form '
             '"path:/<container>/<object>"'
    )
    @magic_arguments.argument(
        '--print-result', action='store_true', default=False,
        help='Print result objet to stdout. Note that this may be a large'
             'binary depends on your app'
    )
    @cell_magic
    def storletapp(self, line, cell):
        args = magic_arguments.parse_argstring(self.storletapp, line)
        module_path = args.module_class
        assert module_path.count('.') == 1
        headers = {
            'X-Object-Meta-Storlet-Language': 'python',
            'X-Object-Meta-Storlet-Interface-Version': '1.0',
            'X-Object-Meta-Storlet-Object-Metadata': 'no',
            'X-Object-Meta-Storlet-Main': module_path,
            'Content-Type': 'application/octet-stream',
        }
        storlet_obj = '%s.py' % module_path.split('.')[0]

        conn = get_swift_connection()
        conn.put_object(args.container, storlet_obj, cell, headers=headers)

        print('Upload storlets succeeded /%s/%s'
              % (args.container, storlet_obj))

        if args.with_invoke:
            if not args.input:
                raise UsageError(
                    '--with-invoke option requires --input to run the app')

            src_container, src_obj = self._parse_input_path(args.input)

            headers = {'X-Run-Storlet': '%s' % storlet_obj}

            # invoke storlet app
            resp_headers, resp_content_iter = conn.get_object(
                src_container, src_obj, resp_chunk_size=64 * 1024,
                headers=headers)

            print('Invocation Complete')
            if args.print_result:
                print('Result Content:')
                print(''.join(resp_content_iter))
            else:
                # drain all resp content stream
                for x in resp_content_iter:
                    pass

    @magic_arguments.magic_arguments()
    @magic_arguments.argument(
        '--input', type=unicode_type,
        help='The input object for the storlet execution'
             'this option must be of the form "path:<container>/<object>"'
    )
    @magic_arguments.argument(
        '--storlet', type=unicode_type,
        help='The storlet to execute over the input'
    )
    @magic_arguments.argument(
        '-i', type=unicode_type,
        help=('A name of a variable defined in the environment '
              'holding a dictionary with the storlet invocation '
              'input parameters')
    )
    @magic_arguments.argument(
        '-o', type=unicode_type,
        help=('A name of an output variable to hold the invocation result '
              'The output variable is a dictionary with the fields: '
              'status, headers, content_iter holding the reponse status, '
              'headers, and body iterator accordingly')
    )
    @line_magic
    def get(self, line):
        args = magic_arguments.parse_argstring(self.get, line)
        if not args.o:
            raise UsageError('-o option is mandatory for the invocation')
        if not args.o[0].startswith(tuple(string.ascii_letters)):
            raise UsageError('The output variable name must be a valid prefix '
                             'of a python variable, that is, start with a '
                             'letter')
        if not args.storlet:
            raise UsageError('--storlet option is mandatory '
                             'for the invocation')
        if not args.input:
            raise UsageError('--input option is mandatory for the invocation')

        src_container, src_obj = self._parse_input_path(args.input)

        headers = {'X-Run-Storlet': '%s' % args.storlet}
        headers.update(self._generate_params_headers(args))

        # invoke storlet app on get
        conn = get_swift_connection()
        response_dict = dict()
        resp_headers, resp_content_iter = conn.get_object(
            src_container, src_obj,
            resp_chunk_size=64 * 1024,
            headers=headers,
            response_dict=response_dict)

        res = dict()
        res['headers'] = resp_headers
        res['content_iter'] = resp_content_iter
        res['status'] = response_dict['status']
        print('Invocation Complete')
        self.shell.user_ns[args.o] = res

    @magic_arguments.magic_arguments()
    @magic_arguments.argument(
        '--input', type=unicode_type,
        help='The input object for the storlet execution'
             'this option must be of the form "path:<container>/<object>"'
    )
    @magic_arguments.argument(
        '--output', type=unicode_type,
        help='The output object for the storlet execution'
             'this option must be of the form "path:<container>/<object>"'
    )
    @magic_arguments.argument(
        '--storlet', type=unicode_type,
        help='The storlet to execute over the input'
    )
    @magic_arguments.argument(
        '-i', type=unicode_type,
        help=('A name of a variable defined in the environment '
              'holding a dictionary with the storlet invocation '
              'input parameters')
    )
    @magic_arguments.argument(
        '-o', type=unicode_type,
        help=('A name of an output variable to hold the invocation result '
              'The output variable is a dictionary with the fields: '
              'status, headers, holding the reponse status and '
              'headers accordingly')
    )
    @magic_arguments.argument(
        '--extra', type=unicode_type,
        help='Specift a comma seperated list of extra resources'
             'this option must be of the form '
             '"<container>/<object>,...,<container>/<object>"'
    )
    @line_magic
    def copy(self, line):
        args = magic_arguments.parse_argstring(self.copy, line)
        if not args.o:
            raise UsageError('-o option is mandatory for the invocation')
        if not args.o[0].startswith(tuple(string.ascii_letters)):
            raise UsageError('The output variable name must be a valid prefix '
                             'of a python variable, that is, start with a '
                             'letter')
        if not args.storlet:
            raise UsageError('--storlet option is mandatory '
                             'for the invocation')
        if not args.input:
            raise UsageError('--input option is mandatory for the invocation')

        if not args.output:
            raise UsageError('--output option is mandatory for the invocation')

        src_container, src_obj = self._parse_input_path(args.input)
        dst_container, dst_obj = self._parse_input_path(args.output)
        destination = '/%s/%s' % (dst_container, dst_obj)

        headers = {'X-Run-Storlet': '%s' % args.storlet}
        headers.update(self._generate_params_headers(args))
        if args.extra:
            headers['X-Storlet-Extra-Resources'] = args.extra

        # invoke storlet app on copy
        conn = get_swift_connection()
        response_dict = dict()
        conn.copy_object(
            src_container, src_obj,
            destination=destination,
            headers=headers,
            response_dict=response_dict)

        res = dict()
        res['headers'] = response_dict['headers']
        res['status'] = response_dict['status']
        self.shell.user_ns[args.o] = res

    @magic_arguments.magic_arguments()
    @magic_arguments.argument(
        '--input', type=unicode_type,
        help='The local input object for upload'
             'this option must be a full path of a local file'
    )
    @magic_arguments.argument(
        '--output', type=unicode_type,
        help='The  output object of the storlet execution'
             'this option must be of the form "path:<container>/<object>"'
    )
    @magic_arguments.argument(
        '--storlet', type=unicode_type,
        help='The storlet to execute over the input'
    )
    @magic_arguments.argument(
        '-i', type=unicode_type,
        help=('A name of a variable defined in the environment '
              'holding a dictionary with the storlet invocation '
              'input parameters')
    )
    @magic_arguments.argument(
        '-o', type=unicode_type,
        help=('A name of an output variable to hold the invocation result '
              'The output variable is a dictionary with the fields: '
              'status, headers, holding the reponse status and '
              'headers accordingly')
    )
    @line_magic
    def put(self, line):
        args = magic_arguments.parse_argstring(self.put, line)
        if not args.o:
            raise UsageError('-o option is mandatory for the invocation')
        if not args.o[0].startswith(tuple(string.ascii_letters)):
            raise UsageError('The output variable name must be a valid prefix '
                             'of a python variable, that is, start with a '
                             'letter')
        if not args.storlet:
            raise UsageError('--storlet option is mandatory '
                             'for the invocation')
        if not args.input:
            raise UsageError('--input option is mandatory for the invocation')
        if not args.input.startswith('/'):
            raise UsageError('--input argument must be a full path')

        if not args.output:
            raise UsageError('--output option is mandatory for the invocation')

        dst_container, dst_obj = self._parse_input_path(args.output)

        headers = {'X-Run-Storlet': '%s' % args.storlet}
        headers.update(self._generate_params_headers(args))

        # invoke storlet app on copy
        conn = get_swift_connection()
        response_dict = dict()
        with open(args.input, 'r') as content:
            resp_headers, resp_content_iter = conn.put_object(
                content,
                dst_container, dst_obj,
                resp_chunk_size=64 * 1024,
                headers=headers,
                response_dict=response_dict)

        res = dict()
        res['headers'] = resp_headers
        res['status'] = response_dict['status']
        print('Invocation Complete')
        self.shell.user_ns[args.o] = res

    @magic_arguments.magic_arguments()
    @magic_arguments.argument(
        '-i', type=unicode_type,
        help=('A name of an input container to read')
    )
    @magic_arguments.argument(
        '-o', type=unicode_type,
        help=('A name of an output variable to hold the container listing')
    )
    @line_magic
    def list_container(self, line):
        args = magic_arguments.parse_argstring(self.list_container, line)
        if not args.i:
            raise UsageError('-i option is mandatory for listing')
        if not args.o:
            raise UsageError('-o option is mandatory for listing')
        if not args.o[0].startswith(tuple(string.ascii_letters)):
            raise UsageError('The output variable name must be a valid prefix '
                             'of a python variable, that is, start with a '
                             'letter')

        # Get the objects
        conn = get_swift_connection()
        _, objects = conn.get_container(
            args.i,
            full_listing=True)

        # Populate the returned list
        obj_names = []
        for obj_dict in objects:
            obj_names.append(obj_dict['name'])
        self.shell.user_ns[args.o] = obj_names

    @magic_arguments.magic_arguments()
    @magic_arguments.argument(
        '-c', type=unicode_type,
        help=('A name of an input container to read')
    )
    @magic_arguments.argument(
        '-v', type=unicode_type,
        help=('A name of an input video to play')
    )
    @line_magic
    def play_video(self, line):
        args = magic_arguments.parse_argstring(self.play_video, line)
        if not args.c:
            raise UsageError('-c option is mandatory')
        if not args.v:
            raise UsageError('-v option is mandatory')

        conn = get_swift_connection()
        resp_headers, resp_content_iter = conn.get_object(
            args.c, args.v)
        video_fname = '/tmp/%s' % args.v
        with open(video_fname,'w') as video_file:
            video_file.write(resp_content_iter)

        play(video_fname)
        os.unlink(video_fname)

    @magic_arguments.magic_arguments()
    @magic_arguments.argument(
        '--input', type=unicode_type,
        help='The input object of an image to show'
             'this option must be of the form "path:<container>/<object>"'
    )
    @line_magic
    def show_image(self, line):
        args = magic_arguments.parse_argstring(self.show_image, line)
        if not args.input:
            raise UsageError('--input option is mandatory')

        src_container, src_obj = self._parse_input_path(args.input)

        # invoke storlet app on get
        conn = get_swift_connection()
        response_dict = dict()
        resp_headers, resp_content_iter = conn.get_object(
            src_container,
            src_obj,
            response_dict=response_dict)
        img_str = ''
        for buf in resp_content_iter:
            img_str += buf
        show_image(img_str)


def load_ipython_extension(ipython):
    ipython.register_magics(StorletMagics)
