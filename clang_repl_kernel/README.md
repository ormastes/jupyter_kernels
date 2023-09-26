Clang-Repl kernel for Jupyter
===========

A simple Jupyter kernel for C/C++ using Clang-Repl.

CAUTION
-------

There is a problem on Windows with Clang-Repl when work with Python.
You need to fix LineEditor.h file.
Put ::fflush(Data->Out); after ::fprintf(Data->Out, "%s", Prompt.c_str()); in LineEditor::readLine()
And rebuild it and put it on PATH or {package installed directory}/{platform}.

OR download https://github.com/ormastes/jupyter_kernels/blob/main/clang_repl_kernel/clang_repl_kernel/Windows/clang-repl.exe
And put it on PATH or {package installed directory}/{platform}. (You may need to rename it to clang-repl.exe)

> package installed directory
> - Windows: C:\Users\{user}\AppData\Local\Programs\Python\Python{version}\Lib\site-packages\clang_repl_kernel
> - Linux: /usr/local/lib/python{version}/dist-packages/clang_repl_kernel
> - MacOS: /Library/Frameworks/Python.framework/Versions/{version}/lib/python{version}/site-packages/clang_repl_kernel

> platform
> - Windows: Windows
> - Linux: Linux
> - MacOS: Darwin

```diff
     llvm/lib/LineEditor/LineEditor.cpp | 1 +
     1 file changed, 1 insertion(+)

    diff --git a/llvm/lib/LineEditor/LineEditor.cpp b/llvm/lib/LineEditor/LineEditor.cpp
    index bb408411a330..15d3ba4dc834 100644
    --- a/llvm/lib/LineEditor/LineEditor.cpp
    +++ b/llvm/lib/LineEditor/LineEditor.cpp
    @@ -294,6 +294,7 @@ void LineEditor::loadHistory() {}

     std::optional<std::string> LineEditor::readLine() const {
       ::fprintf(Data->Out, "%s", Prompt.c_str());
    +  ::fflush(Data->Out);

       std::string Line;
       do {
```

From Pip to install
-------------------

To install ``clang_repl_kernel`` from pip into the active Python environment

```bash
    pip install clang_repl_kernel
```

From Git using Conda
--------------------

To install ``clang_repl_kernel`` from git into a Conda environment
```basg
    git clone https://github.com/ormastes/jupyter_kernels/clang_repl_kernel.git
    cd clang_repl_kernel
    conda create -n ker jupyter
    conda activate ker
    pip install .
```

Using the Clang-Repl kernel
---------------------
**Notebook**: The *File* > *New* > *Notebook* menu in the notebook should show an Kernel Selection for the notebook.
Select kernel ''Clang-Repl (C++xx)'' to start a new notebook. (XX is the version of C++ you want to use)

**Console frontends**: To use it with the console frontends, add ``--kernel clang_repl_cppXX`` to their command line arguments.
(XX is the version of C++ you want to use)

It fully checked on Windows 11 with clang 18.0.0 and Python 3.11.5

Reference
---------
https://github.com/jupyter/echo_kernel
https://saturncloud.io/blog/how-to-add-a-python-3-kernel-to-jupyter-ipython/
https://github.com/takluyver/bash_kernel
