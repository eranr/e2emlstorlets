# Copyright (c) 2016 Satya Mallic (learnopencv)
# Copyright (c) 2015 Matthew Earl

import os
import sys
import numpy as np
import cv2
import dlib
import threading

PREDICTOR_PATH = "/opt/shape_predictor_68_face_landmarks.dat"
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(PREDICTOR_PATH)

def get_landmarks(im):
    rects = detector(im, 1)

    if len(rects) > 1:
        raise TooManyFaces
    if len(rects) == 0:
        raise NoFaces

    return [(p.x, p.y) for p in predictor(im, rects[0]).parts()]

# Apply affine transform calculated using srcTri and dstTri to src and
# output an image of size.
def applyAffineTransform(src, srcTri, dstTri, size) :

    # Given a pair of triangles, find the affine transform.
    warpMat = cv2.getAffineTransform( np.float32(srcTri), np.float32(dstTri) )

    # Apply the Affine Transform just found to the src image
    dst = cv2.warpAffine( src, warpMat, (size[0], size[1]), None, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101 )

    return dst


# Check if a point is inside a rectangle
def rectContains(rect, point) :
    if point[0] < rect[0] :
        return False
    elif point[1] < rect[1] :
        return False
    elif point[0] > rect[0] + rect[2] :
        return False
    elif point[1] > rect[1] + rect[3] :
        return False
    return True

#calculate delanauy triangle
def calculateDelaunayTriangles(rect, points):
    #create subdiv
    subdiv = cv2.Subdiv2D(rect);

    # Insert points into subdiv
    for p in points:
        subdiv.insert(p)

    triangleList = subdiv.getTriangleList();

    delaunayTri = []

    pt = []

    count= 0

    for t in triangleList:
        pt.append((t[0], t[1]))
        pt.append((t[2], t[3]))
        pt.append((t[4], t[5]))

        pt1 = (t[0], t[1])
        pt2 = (t[2], t[3])
        pt3 = (t[4], t[5])

        if rectContains(rect, pt1) and rectContains(rect, pt2) and rectContains(rect, pt3):
            count = count + 1
            ind = []
            for j in xrange(0, 3):
                for k in xrange(0, len(points)):
                    if(abs(pt[j][0] - points[k][0]) < 1.0 and abs(pt[j][1] - points[k][1]) < 1.0):
                        ind.append(k)
            if len(ind) == 3:
                delaunayTri.append((ind[0], ind[1], ind[2]))

        pt = []


    return delaunayTri


# Warps and alpha blends triangular regions from img1 and img2 to img
def warpTriangle(img1, img2, t1, t2) :

    # Find bounding rectangle for each triangle
    r1 = cv2.boundingRect(np.float32([t1]))
    r2 = cv2.boundingRect(np.float32([t2]))

    # Offset points by left top corner of the respective rectangles
    t1Rect = []
    t2Rect = []
    t2RectInt = []

    for i in xrange(0, 3):
        t1Rect.append(((t1[i][0] - r1[0]),(t1[i][1] - r1[1])))
        t2Rect.append(((t2[i][0] - r2[0]),(t2[i][1] - r2[1])))
        t2RectInt.append(((t2[i][0] - r2[0]),(t2[i][1] - r2[1])))


    # Get mask by filling triangle
    mask = np.zeros((r2[3], r2[2], 3), dtype = np.float32)
    cv2.fillConvexPoly(mask, np.int32(t2RectInt), (1.0, 1.0, 1.0), 16, 0);

    # Apply warpImage to small rectangular patches
    img1Rect = img1[r1[1]:r1[1] + r1[3], r1[0]:r1[0] + r1[2]]

    size = (r2[2], r2[3])

    img2Rect = applyAffineTransform(img1Rect, t1Rect, t2Rect, size)

    img2Rect = img2Rect * mask

    # Copy triangular region of the rectangular patch to the output image
    img2[r2[1]:r2[1]+r2[3], r2[0]:r2[0]+r2[2]] = img2[r2[1]:r2[1]+r2[3], r2[0]:r2[0]+r2[2]] * ( (1.0, 1.0, 1.0) - mask )
    img2[r2[1]:r2[1]+r2[3], r2[0]:r2[0]+r2[2]] = img2[r2[1]:r2[1]+r2[3], r2[0]:r2[0]+r2[2]] + img2Rect

def swap_face(img2, img1):
    img1Warped = np.copy(img2);

    # Read array of corresponding points
    points1 = get_landmarks(img1)
    points2 = get_landmarks(img2)

    # Find convex hull
    hull1 = []
    hull2 = []
    hullIndex = cv2.convexHull(np.array(points2), returnPoints = False)

    for i in xrange(0, len(hullIndex)):
        hull1.append(points1[hullIndex[i]])
        hull2.append(points2[hullIndex[i]])


    # Find delanauy traingulation for convex hull points
    sizeImg2 = img2.shape
    rect = (0, 0, sizeImg2[1], sizeImg2[0])
    dt = calculateDelaunayTriangles(rect, hull2)
    if len(dt) == 0:
        raise Exception('dt is empty')

    # Apply affine transformation to Delaunay triangles
    for i in xrange(0, len(dt)):
        t1 = []
        t2 = []

        #get points for img1, img2 corresponding to the triangles
        for j in xrange(0, 3):
            t1.append(hull1[dt[i][j]])
            t2.append(hull2[dt[i][j]])

        warpTriangle(img1, img1Warped, t1, t2)

    # Calculate Mask
    hull8U = []
    for i in xrange(0, len(hull2)):
        hull8U.append((hull2[i][0], hull2[i][1]))

    mask = np.zeros(img2.shape, dtype = img2.dtype)
    cv2.fillConvexPoly(mask, np.int32(hull8U), (255, 255, 255))
    r = cv2.boundingRect(np.float32([hull2]))
    center = ((r[0]+int(r[2]/2), r[1]+int(r[3]/2)))

    # Clone seamlessly.
    output = cv2.seamlessClone(np.uint8(img1Warped), img2, mask, center, cv2.NORMAL_CLONE)
    return output

def crop(img, rect):
    h = rect[3]-rect[1]
    w = rect[2]-rect[0]
    x = rect[0]
    y = rect[1]
    return img[y:y+h, x:x+w]


def recognize_face(frame, model, id_to_name):
    cascade = cv2.CascadeClassifier("/usr/local/share/OpenCV/haarcascades/haarcascade_frontalface_alt.xml")
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rects = cascade.detectMultiScale(gray_frame)
    if len(rects) == 0:
        return [], mat
    rects[:, 2:] += rects[:, :2]
    face = crop(gray_frame, rects[0])
    small_face = cv2.resize(face, (30,30))
    small_face_array = np.asarray(small_face[:,:])
    small_face_vec = small_face_array.reshape(1,900)
    face_id = model.predict(small_face_vec)
    return id_to_name[round(face_id)]


def id_to_name_dict(name_to_id):
    id_to_name = dict()
    for k, v in name_to_id:
        id_to_name[v] = k

    return id_to_name

@contextmanager
def avi_fifo(name):
    try:
        os.mkfifo(name, 0666)
    except OSError as e:
        if e.errno == 17:
            os.unlink(name)
            os.mkfifo(name, 0666)

    try:
        yield
    finally:
        os.unlink(name)

class fifo_worker(threading.Thread):
    def __init__(self, output, fifo_name, logger):
        threading.Thread.__init__(self)
        self.output = output
        self.fifo_name = fifo_name
        self.logger = logger

    def run(self):
        fd = os.open(self.fifo_name, os.O_RDONLY)
        self.logger.debug('fifo %d is opened for reading\n' % fd)

        while(True):
            try:
                chunk = os.read(fd, 1024*64)
                if len(chunk)>0:
                    output.write(chunk)
                else:
                    self.logger.debug('empty chunk\n')
                    break
            except OSError as e:
                break

        os.close(fd)
        self.logger.debug('fifo worker exits\n')

def main_loop(cap, capo, face, logger):
    while(True):
        ret, frame = cap.read()
        out_image = frame

        # Calculate output frame
        if ret==True:
            out_image = swap_face(frame, face)
            out_image = out_image.astype(np.uint8)
            capo.write(out_image)
        else:
            logger.debug('No more frames. Exiting\n')
            break

class MovieSwapFace(object):
    def __init__(self, logger):
        self.logger = logger

    def __call__(self, in_files, out_files, params):
        """
        in_files[0] is assumed to be the movie
        in_files[1] is assumed to be the face to swap with
        """
        out_files[0].set_metadata(in_files[0].get_metadata())
        movie_file = in_files[0]
        movie_fd = movie_file.fileno()
        face_file = in_files[1]


        face_im_buf = ''
        while True:
            buf = face_file.read(1024)
            if not buf:
                break
            face_im_buf += buf   
        self.logger.debug('face read\n')
        face_im_nparr = np.fromstring(face_im_buf, np.uint8)
        face_im = cv2.imdecode(face_im_nparr, cv2.IMREAD_COLOR)
        face_file.close()
        self.logger.debug('face decoded\n')

        fifo_name = 'fifo_%s.avi' % str(os.getpid())
        with avi_fifo(fifo_name):
            worker = fifo_worker(dest_movie, fifo_name,
                                 fifo_name, self.logger)
            worker.start()

            cap = cv2.VideoCapture('pipe:%d' % movie_fd, cv2.CAP_FFMPEG)
            self.logger.debug('movie reader opened\n')
            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            fps = cap.get(cv2.CAP_PROP_FPS)
            fps=int(fps)
            width=int(width)
            height=int(height)
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            capo = cv2.VideoWriter()
            capo.open(fifo_name, fourcc, fps, (width,height))
            self.logger.debug('movie writer opened\n')

            try:
                main_loop(cap, capo, face_im, self.logger)
            except Exception as e:
                self.logger.debug('main_loop exception %s\n' % str(e))
                raise
            finally:
                capo.release()
                self.logger.debug('Awaiting worker thread to finish\n')
                worker.join()
                self.logger.debug('Worker thread finished\n')

        os.close(fdi)
        cap.release()
        movie_file.close()
        self.logger.debug('Done.')
