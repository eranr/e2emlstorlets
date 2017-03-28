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
./prepare_machine.sh
```

This will install Swift and Storlets on the VM together with
a docker container that has the all the necessary packages
for running the storlets in the repo.
Those packages include: opencv, scikit-learn and dlib

In addition the prepare_machine.sh will install all the necessary
packages to run jupyter and the demo notebook.

# Running the demo

```
sudo python setup.py install
python upload_data.py create
jupyter notebook --no-browser --ip=<host ip>
```

Follow the output of the "jupyter_notebook" instruction above
to connect from a browser. From the browser, open the notebook:
"e2emlstorlets/e2e-demo-swift.ipynb"

These instructions do not cover the last part of the demo which
compares run time with AWS S3.

# Copyright Notice
The code behind the face swap is a combination of code borrowed from
Satya Mallic [0], [1] and from Matthew Earl [2], [3]

[0] http://www.learnopencv.com/face-swap-using-opencv-c-python/
[1] https://github.com/spmallick/learnopencv/tree/master/FaceSwap
[2] http://matthewearl.github.io/2015/07/28/switching-eds-with-python/
[3] https://github.com/matthewearl/faceswap/blob/master/faceswap.py

