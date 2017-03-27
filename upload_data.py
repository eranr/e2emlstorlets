import sys
from swiftclient import client
from os import listdir
from os.path import isfile, join
from e2emlstorlets.tools.swift_access import parse_config,\
    get_auth, put_local_file, deploy_storlet


class DemoData():
    def __init__(self, conf_path):
        self.conf = parse_config(conf_path)
        self.url, self.token = get_auth(self.conf) 

    def upload_data_files(self, local_path, container_name):
        client.put_container(self.url, self.token,
                             container_name)
        onlyfiles = [f for f in listdir(local_path) \
                     if isfile(join(local_path, f))]

        for f in onlyfiles:
            fname = '%s/%s' % (local_path, f)
            name = f[:f.find('.')]
            name = ''.join([i for i in name if not i.isdigit()])
            headers = {'X-Object-Meta-name': name,
                       'X-Object-Meta-filename': f}
            with open(fname,'r') as buf:
                client.put_object(self.url, self.token,
                                  container_name, f, buf,
                                  headers=headers)

    def _upload_video(self, local_path, container_name, obj_name):
        with open(local_path,'r') as buf:
            client.put_object(self.url, self.token,
                              'video', obj_name,
                              buf)

    def upload_video(self):
        client.put_container(self.url, self.token,
                             'video')
        self._upload_video('test/data/eran_mov.avi', 'video',  'eran_mov.avi')
        self._upload_video('data/test/bibi_mov.avi', 'test', 'bibi_mov.avi')
        self._upload_video('data/test/merkel_mov.avi', 'test',  'merkel_mov.avi')
        self._upload_video('data/test/trump_mov.avi', 'test', 'trump_mov.avi')
        self._upload_video('data/test/obama_mov.avi', 'test', 'obama_mov.avi')

    def upload_storlets(self):
        deploy_storlet(self.conf,
                       'e2emlstorlets/extract_face/extract_face.py',
                       'extract_face.ExtractFace')
        deploy_storlet(self.conf,
                       'e2emlstorlets/train_model/train_model.py',
                       'train_model.TrainModel')
        deploy_storlet(self.conf,
                       'e2emlstorlets/video_recognize_face/video_recognize_face.py',
                       'video_recognize_face.MovieRecognizeFace')
        deploy_storlet(self.conf,
                       'e2emlstorlets/video_swap_face/video_swap_face.py',
                       'video_swap_face.MovieSwapFace')

    def create_other_containers(self):
        client.put_container(self.url, self.token,
                             'trained')
        client.put_container(self.url, self.token,
                             'extracted')

    def clean_container(self, container_name):
        _, objects = client.get_container(
            self.url, self.token, container_name,
            full_listing=True)

        # delete all objects inside the container
        # N.B. this cleanup could run in parallel but currently we have a few
        # objects in the user testing container so that, currently this does
        # as sequential simply
        for obj_dict in objects:
            client.delete_object(
                self.url, self.token,
                container_name, obj_dict['name'])
        client.get_container(self.url, self.token, container_name)

        # delete the container
        client.delete_container(self.url, self.token, container_name)    

    def create_demo_data(self):
        self.upload_data_files('data/train','train')
        self.upload_data_files('data/test','test')
        self.upload_video()
        self.upload_storlets()
        self.create_other_containers()


    def delete_demo_data(self):
        self.clean_container('train')
        self.clean_container('test')
        self.clean_container('extracted')
        self.clean_container('video')
        self.clean_container('trained')
        client.delete_object(self.url, self.token, 'storlet',
                             'extract_face.py')
        client.delete_object(self.url, self.token, 'storlet',
                             'train_model.py')
        client.delete_object(self.url, self.token, 'storlet',
                             'video_swap_face.py')
        client.delete_object(self.url, self.token, 'storlet',
                             'video_recognize_face.py')

if len(sys.argv) != 2:
    print('Usage: create | delete')
    exit()


op = sys.argv[1]
data = DemoData('access.cfg')
if op == 'create':
    data.create_demo_data()
elif op == 'delete':
    data.delete_demo_data()
else:
    print('Usage: create | delete')
