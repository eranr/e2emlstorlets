import sys
import boto3
from os import listdir
from os.path import isfile, join


class DemoData():
    def __init__(self, conf_path):
        self.client = boto3.client('s3')
        pass

    def upload_train_files(self, local_path):
        onlyfiles = [f for f in listdir(local_path) \
                     if isfile(join(local_path, f))]

        for f in onlyfiles:
            fname = '%s/%s' % (local_path, f)
            with open(fname,'r') as buf:
                response = self.client.put_object(
                    Body=buf,
                    Bucket='e2emlstorlets-train',
                    Key=f)
                print response

    def upload_test_files(self, local_path):
        onlyfiles = [f for f in listdir(local_path) \
                     if isfile(join(local_path, f))]

        for f in onlyfiles:
            fname = '%s/%s' % (local_path, f)
            with open(fname,'r') as buf:
                response = self.client.put_object(
                    Body=buf,
                    Bucket='e2emlstorlets-test',
                    Key=f)
                print response

    def upload_video(self):
        self.client.create_bucket(Bucket='e2emlstorlets-video')
        with open('test/data/eran_mov.avi','r') as buf:
            self.client.put_object(
                              Body=buf,
                              Bucket='e2emlstorlets-video',
                              Key='eran_mov.avi')

    def create_other_containers(self):
        self.client.create_bucket(Bucket='e2emlstorlets-trained')
        self.client.create_bucket(Bucket='e2emlstorlets-small-train')

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
        #self.upload_train_files('data/train')
        self.upload_test_files('data/test')
        #self.upload_video()
        #self.create_other_containers()

    def delete_demo_data(self):
        pass

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
