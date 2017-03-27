#git clone https://github.com/openstack/storlets ~/storlets
#cd ~/storlets
#./s2aio.sh dev host

NUM_IMAGES=`sudo docker images | grep  -v ubuntu | grep -v REPOSITORY | awk '{print $1}' | wc -l`

if [ $NUM_IMAGES != 1 ]; then
    echo "Cannot determine the project id. Please execute install.sh [project id]"
    exit
fi

PROJECT_ID=`sudo docker images | grep  -v ubuntu | grep -v REPOSITORY | awk '{print $1}'`

mkdir -p /tmp/update_docker_image
cd /tmp/update_docker_image
wget http://sourceforge.net/projects/dclib/files/dlib/v18.10/shape_predictor_68_face_landmarks.dat.bz2
bzip2 -d shape_predictor_68_face_landmarks.dat.bz2
cd -

cat <<EOF >/tmp/update_docker_image/Dockerfile
FROM $PROJECT_ID

MAINTAINER root

# The following operations should be defined in one line
# to prevent docker images from including apt cache file.
RUN apt-get update && \
    apt-get install cmake -y && \
    pip install numpy==1.11.3 && \
    apt-get install python-scipy -y && \
    pip install scikit-learn==0.18 && \
    apt-get install libboost-all-dev -y && \
    pip install dlib && \
    apt-get install --assume-yes build-essential cmake git qt5-default && \
    apt-get install --assume-yes build-essential pkg-config unzip ffmpeg qtbase5-dev python-dev && \
    apt-get install --assume-yes libopencv-dev libgtk-3-dev libdc1394-22 libdc1394-22-dev libjpeg-dev libpng12-dev libtiff5-dev libjasper-dev && \
    apt-get install --assume-yes libavcodec-dev libavformat-dev libswscale-dev libxine2-dev libgstreamer0.10-dev libgstreamer-plugins-base0.10-dev && \
    apt-get install --assume-yes libv4l-dev libtbb-dev libmp3lame-dev libopencore-amrnb-dev libopencore-amrwb-dev libtheora-dev && \
    apt-get install --assume-yes libvorbis-dev libxvidcore-dev v4l-utils && \
    git clone https://github.com/opencv/opencv.git && \
    cd opencv && \
    mkdir build && \
    cd build/ && \
    cmake -D CMAKE_BUILD_TYPE=RELEASE -D CMAKE_INSTALL_PREFIX=/usr/local -D WITH_TBB=ON -D WITH_V4L=ON -D WITH_QT=ON -D WITH_OPENGL=ON -D WITH_CUBLAS=ON -DCUDA_NVCC_FLAGS="-D_FORCE_INLINES" .. && \
    make -j $(($(nproc) + 1)) && \
    make install && \
    /bin/bash -c 'echo "/usr/local/lib" > /etc/ld.so.conf.d/opencv.conf' && \
    ldconfig && \
    apt-get update 

COPY shape_predictor_68_face_landmarks.dat /opt/

EOF

sudo docker build -t e2emlstorlets /tmp/update_docker_image
IMAGE_ID=`sudo docker images | grep e2emlstorlets | awk '{print $3}'`
sudo docker rmi $PROJECT_ID
sudo docker tag $IMAGE_ID ${PROJECT_ID:0:13}
sudo docker rmi e2emlstorlets

rm -fr /tmp/update_docker_image
