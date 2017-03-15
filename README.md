# e2emlstorlets
Storlets and Jupyter notebook demonstrating end to end machine learning with storlets
using IPython

# Installation
On a fresh new 16.04 VM with apasswordless sudoer simply:

```
git clone https://github.com/eranr/e2emlstorlets.git
cd e2emlstorlets
./install.sh
tox -e functional
```

This will install Swift and Storlets on the VM together with
a docker container that has the all the necessary packages
for running the storlets in the repo.
Those packages include: opencv, scikit-learn and dlib

# Copyright Notice
The code behind the face swap is a combination of code borrowed from
Satya Mallic [0], [1] and from Matthew Earl [2], [3]

[0] http://www.learnopencv.com/face-swap-using-opencv-c-python/
[1] https://github.com/spmallick/learnopencv/tree/master/FaceSwap
[2] http://matthewearl.github.io/2015/07/28/switching-eds-with-python/
[3] https://github.com/matthewearl/faceswap/blob/master/faceswap.py
