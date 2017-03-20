import sys
import cv2
import json
import boto3
import pickle
import numpy as np
import sklearn.neural_network as snn


def build_traning_data(client, name_to_id):
    response = client.list_objects(Bucket='e2emlstorlets-small-train')
    if response['IsTruncated']==True:
        raise Exception('Truncated Bucket')
    num_files = len(response['Contents'])
    X = np.ndarray(shape=(num_files,30*30), dtype=np.int32)
    y = np.ndarray(shape=(num_files,), dtype=np.int32)

    
    i = 0
    for obj in response['Contents']:
        objName = obj['Key']
        res = client.get_object(Bucket='e2emlstorlets-small-train',
                                Key=objName)
        leader_name = res['Metadata']['name']
        print('Adding %s of size %d to training set' % (objName, res['ContentLength']))
        img_str = res['Body'].read()
        img_nparray = np.fromstring(img_str, np.uint8)
        image_mat = cv2.imdecode(img_nparray, cv2.IMREAD_GRAYSCALE)
        image_array = np.asarray(image_mat[:,:])
        image_vec = image_array.reshape(1,900)
        X[i,:] = image_vec
        y[i] = name_to_id[leader_name]
        i=i+1

    return X, y

def train_model(X, y):
    regressor = snn.MLPRegressor(
        hidden_layer_sizes=(100,),
        activation='logistic',
        solver='lbfgs',
        max_iter=1000)
    regressor.fit(X,y)
    return regressor

def upload_model(client, model_path, name_to_id):
    with open(model_path, 'r') as f:
        client.put_object(Bucket='e2emlstorlets-trained',
                          Body=f,
                          Key='model',
                          Metadata={'name_to_id': json.dumps(name_to_id)})


def train_and_upload_model():
    client = boto3.client('s3')
    name_to_id={'bibi': 1, 'merkel': 2, 'obama': 3, 'trump': 4}
    print('Building training set from data on S3')
    X, y = build_traning_data(client, name_to_id)

    print('Training model')
    model = train_model(X, y)
    with open('/tmp/model', 'w') as fmodel:
        pickle.dump(model, fmodel)

    print('Uploading trained model')
    upload_model(client, '/tmp/model', name_to_id)

def main():
    train_and_upload_model()

if __name__ == "__main__":
    sys.exit(main())
