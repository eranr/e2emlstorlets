import sys
import cv2
import boto3

from e2emlstorlets.training_constants import *

def detect(im):
    mat=cv2.imdecode(im, cv2.IMREAD_GRAYSCALE)
    cascade = cv2.CascadeClassifier("/usr/local/share/OpenCV/haarcascades/haarcascade_frontalface_alt.xml")
    rects = cascade.detectMultiScale(mat)

    if len(rects) == 0:
        return [], mat
    rects[:, 2:] += rects[:, :2]
    rect = rects[0]
    return mat, rect

def crop(img, rect):
    h = rect[3]-rect[1]
    w = rect[2]-rect[0]
    x = rect[0]
    y = rect[1]
    # account for forehead part
    hm = height_frac * h
    hm = int(hm)
    if y >= hm:
        cropped = img[y-hm:y+h, x:x+w]
    else:
        h = h + (hm - y)
        hm = y
        cropped = img[y-hm:y+h, x:x+w]
    return cropped


def get_name(obj_name):
    name = obj_name[:obj_name.find('.')]
    name = ''.join([i for i in name if not i.isdigit()])
    return name

def extract_face(path, outpath):
    mat=cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    cascade = cv2.CascadeClassifier("/usr/local/share/OpenCV/haarcascades/haarcascade_frontalface_alt.xml")
    rects = cascade.detectMultiScale(mat)

    if len(rects) == 0:
        return [], mat
    rects[:, 2:] += rects[:, :2]
    rect = rects[0]

    face = crop(mat, rect)
    small_face = cv2.resize(face, (width,height))
    cv2.imwrite(outpath, small_face)

def extract_and_upload_all():
    client = boto3.client('s3')
    
    response = client.list_objects(Bucket='e2emlstorlets-train')
    if response['IsTruncated']==True:
        raise Exception('Truncated Bucket')
    
    for obj in response['Contents']:
        objName = obj['Key']
        smallObjName='small_%s' % objName
        localName = '/tmp/%s' % objName
        localOutName='/tmp/small_%s' % objName
        leader_name = get_name(objName)
    
        #download file
        print('Downloading %s' % objName)
        res = client.get_object(Bucket='e2emlstorlets-train',
                                Key=objName)
        with open(localName, 'w') as local:
            local.write(res['Body'].read())
    
        #extract face
        print('Processing %s' % objName)
        extract_face(localName, localOutName)
    
        #upload result
        print('Uploading %s' % smallObjName)
        with open(localOutName,'r') as f:
            client.put_object(Bucket='e2emlstorlets-small-train',
                              Body=f.read(),
                              Key=smallObjName,
                              Metadata={'name': leader_name})

def main():
    extract_and_upload_all()

if __name__ == "__main__":
    sys.exit(main())
