import sys
import cv2
import json
import boto3
import pickle
import numpy as np
import sklearn.neural_network as snn
from random import shuffle
from e2emlstorlets.training_constants import *


def build_traning_data(client):
    response = client.list_objects(Bucket='e2emlstorlets-small-train')
    if response['IsTruncated']==True:
        raise Exception('Truncated Bucket')
    num_files = len(response['Contents'])
    X = np.ndarray(shape=(num_files,width*height), dtype=np.int32)
    y = np.ndarray(shape=(num_files,), dtype='|S6')

    i = 0
    objects = response['Contents']
    shuffle(objects)
    for obj in objects:
        objName = obj['Key']
        res = client.get_object(Bucket='e2emlstorlets-small-train',
                                Key=objName)
        leader_name = res['Metadata']['name']
        print('Adding %s of size %d to training set' % (objName, res['ContentLength']))
        img_str = res['Body'].read()
        img_nparray = np.fromstring(img_str, np.uint8)
        image_mat = cv2.imdecode(img_nparray, cv2.IMREAD_GRAYSCALE)
        image_array = np.asarray(image_mat[:,:])
        image_vec = image_array.reshape(1,2750)
        X[i,:] = image_vec
        y[i] = leader_name
        i=i+1

    return X, y

def train_model(X, y):
    classifier = snn.MLPClassifier(
        hidden_layer_sizes=hidden_layers_sizes,
        activation=activation,
        solver=solver,
        max_iter=max_iter,
        alpha=alpha,
        tol=tolerance,
        random_state=random_state)
    classifier.fit(X,y)
    return classifier

def upload_model(client, model_path):
    with open(model_path, 'r') as f:
        client.put_object(Bucket='e2emlstorlets-trained',
                          Body=f,
                          Key='model')


def train_and_upload_model():
    client = boto3.client('s3')
    print('Building training set from data on S3')
    X, y = build_traning_data(client)

    print('Training model')
    model = train_model(X, y)
    with open('/tmp/model', 'w') as fmodel:
        pickle.dump(model, fmodel)

    print('Uploading trained model')
    upload_model(client, '/tmp/model')

def main():
    train_and_upload_model()

if __name__ == "__main__":
    sys.exit(main())
