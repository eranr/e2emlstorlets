sudo pip install python-numpy==1.11.3 -y
sudo apt-get install python-scipy -y
sudo pip install scikit-learn==0.18
sudo apt-get install libboost-all-dev -y
sudo pip install dlib
sudo pip install jupyter
sudo apt-get install cmake -y
sudo apt-get install qt5-default -y
sudo apt-get install --assume-yes build-essential pkg-config unzip ffmpeg qtbase5-dev python-dev
sudo apt-get install --assume-yes libopencv-dev libgtk-3-dev libdc1394-22 libdc1394-22-dev libjpeg-dev libpng12-dev libtiff5-dev libjasper-dev
sudo apt-get install --assume-yes libavcodec-dev libavformat-dev libswscale-dev libxine2-dev libgstreamer0.10-dev libgstreamer-plugins-base0.10-dev
sudo apt-get install --assume-yes libv4l-dev libtbb-dev libmp3lame-dev libopencore-amrnb-dev libopencore-amrwb-dev libtheora-dev
sudo apt-get install --assume-yes libvorbis-dev libxvidcore-dev v4l-utils
sudo apt-get install libboost-all-dev -y
sudo pip install dlib
sudo pip install matplotlib
sudo pip install boto3
sudo apt-get install python-tk
wget http://sourceforge.net/projects/dclib/files/dlib/v18.10/shape_predictor_68_face_landmarks.dat.bz2
bzip2 -d shape_predictor_68_face_landmarks.dat.bz2
sudo mv shape_predictor_68_face_landmarks.dat /opt/
pushd .
cd ~
git clone https://github.com/opencv/opencv.git
cd opencv
mkdir build
cd build
cmake -D CMAKE_BUILD_TYPE=RELEASE -D CMAKE_INSTALL_PREFIX=/usr/local -D WITH_TBB=ON -D WITH_V4L=ON -D WITH_QT=ON -D WITH_OPENGL=ON -D WITH_CUBLAS=ON -DCUDA_NVCC_FLAGS="-D_FORCE_INLINES" ..
make -j $(($(nproc) + 1))
sudo make install
sudo /bin/bash -c 'echo "/usr/local/lib" > /etc/ld.so.conf.d/opencv.conf'
sudo ldconfig
popd
