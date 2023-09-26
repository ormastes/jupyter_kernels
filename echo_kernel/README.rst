my_echo_kernel
===========

rewrite of echo_kernel(https://github.com/jupyter/echo_kernel) example.

From Git using Conda
~~~~~~~~~~~~~~~~~~~~

To install ``echo_kernel`` from git into a Conda environment::

    # git clone ... echo_kernel TODO
    cd echo_kernel
    conda create -n ker jupyter
    conda activate ker
    pip install .


Using the Echo kernel
---------------------
**Notebook**: The *New* menu in the notebook should show an option for an Echo notebook.

**Console frontends**: To use it with the console frontends, add ``--kernel echo`` to
their command line arguments.

Reference
---------
https://github.com/jupyter/echo_kernel
https://saturncloud.io/blog/how-to-add-a-python-3-kernel-to-jupyter-ipython/
https://github.com/takluyver/bash_kernel
