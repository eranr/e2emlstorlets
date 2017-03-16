sudo apt-get install python-numpy -y
sudo apt-get install python-scipy -y
sudo pip install scikit-learn==0.18
sudo apt-get install libboost-all-dev -y
sudo pip install dlib
sudo pip install jupyter
sudo apt-get install cmake -y
sudo apt-get install qt5-default -y
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
