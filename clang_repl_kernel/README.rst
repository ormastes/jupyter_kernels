Clang-Repl kernel for Jupyter
===========

A simple Jupyter kernel for C/C++ using Clang-Repl.

From Pip to install
~~~~~~~~~~~~~~~~~~~~

To install ``clang_repl_kernel`` from pip into the active Python environment::

    pip install clang_repl_kernel

From Git using Conda
~~~~~~~~~~~~~~~~~~~~

To install ``clang_repl_kernel`` from git into a Conda environment::

    git clone https://github.com/ormastes/jupyter_kernels/clang_repl_kernel.git
    cd clang_repl_kernel
    conda create -n ker jupyter
    conda activate ker
    pip install .

Using the Clang-Repl kernel
---------------------
**Notebook**: The *File* > *New* > *Notebook* menu in the notebook should show an Kernel Selection for the notebook.
Select kernel ''Clang-Repl (C++xx)'' to start a new notebook. (XX is the version of C++ you want to use)

**Console frontends**: To use it with the console frontends, add ``--kernel clang_repl_cppXX`` to their command line arguments.
(XX is the version of C++ you want to use)

Reference
---------
https://github.com/jupyter/echo_kernel
https://saturncloud.io/blog/how-to-add-a-python-3-kernel-to-jupyter-ipython/
https://github.com/takluyver/bash_kernel
