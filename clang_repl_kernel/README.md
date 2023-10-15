Clang-Repl kernel for Jupyter
===========

A simple Jupyter kernel for C/C++ using Clang-Repl.
It works on Windows and Linux. (MacOS is not tested)

See: [Clang-Repl](https://clang.llvm.org/docs/ClangRepl.html)


Please use Python 3.11 or higher. (3.12 is recommended)

* Windows 11
python3 3.12.0
Selected Jupyter core packages...
IPython          : 8.16.1
ipykernel        : 6.25.2
ipywidgets       : not installed
jupyter_client   : 8.4.0
jupyter_core     : 5.4.0
jupyter_server   : 2.7.3
jupyterlab       : 4.0.7
nbclient         : 0.8.0
nbconvert        : 7.9.2
nbformat         : 5.9.2
notebook         : 7.0.5
qtconsole        : not installed
traitlets        : 5.11.2

* Ubuntu 22.04
python3 3.12
IPython          : 8.16.1
ipykernel        : 6.25.2
ipywidgets       : not installed
jupyter_client   : 8.4.0
jupyter_core     : 5.4.0
jupyter_server   : 2.7.3
jupyterlab       : 4.0.7
nbclient         : 0.8.0
nbconvert        : 7.9.2
nbformat         : 5.9.2
notebook         : 7.0.5
qtconsole        : not installed
traitlets        : 5.11.2
  
See: [How to Install Python 3.12 on Ubuntu 22.04 - LinuxTuto](https://www.linuxtuto.com/how-to-install-python-3-12-on-ubuntu-22-04/)
See: [Setting the Default python to python3 | Baeldung on Linux](https://www.baeldung.com/linux/default-python3)


CAUTION
-------

There is a problem on Windows with Clang-Repl when work with Python.
You need to fix LineEditor.h file.
Put ::fflush(Data->Out); after ::fprintf(Data->Out, "%s", Prompt.c_str()); in LineEditor::readLine()
And rebuild it and put it on PATH or {package installed directory}/{platform}.

OR **download** one of 
windows: https://github.com/ormastes/jupyter_kernels/blob/main/clang_repl_kernel/clang_repl_kernel/Windows/clang-repl.exe
linux: https://github.com/ormastes/jupyter_kernels/blob/main/clang_repl_kernel/clang_repl_kernel/Linux/clang-repl
And put it on PATH or **{package installed directory}/{platform}**. (You may need to rename it to clang-repl.exe or clang-repl)
However, you need to **install** 
windows: Visual Studio 2022 c++ (https://visualstudio.microsoft.com/downloads/)
linux: build-essential (sudo apt install build-essential, git clone https://github.com/llvm/llvm-project.git)

> package installed directory
> - Windows: C:\Users\{user}\AppData\Local\Programs\Python\Python{version}\Lib\site-packages\clang_repl_kernel
> - Linux: /usr/local/lib/python{version}/dist-packages/clang_repl_kernel
>   - or /home/{user}/.local/lib/python{version}/site-packages/clang_repl_kernel/
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

Trouble shot
------------
When you see 
```bash
/usr/include/stdio.h:33:10: fatal error: 'stddef.h' file not found
   33 | #include <stddef.h>
      |          ^~~~~~~~~~
Segmentation fault
```
put path include 'stddef.h' file like and uninstall and reinstall clang-repl-kernel
(You need to change llvm-18 to your llvm)
```bash
export CPLUS_INCLUDE_PATH=/usr/lib/llvm-18/lib/clang/18/include/
pip uninstall clang_repl_kernel
pip install clang_repl_kernel
```

When you see
```bash
ModuleNotFoundError: No module named 'ipykernel'
```

Use venv or conda environment and install notebook
```bash
python -m venv venv
source venv/bin/activate
pip install notebook
pip -r requirements.txt
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

It fully checked on Windows 11 with clang 18.0.0, Python 3.11.5 and notebook 7.0.4.
It fully checked on Ubuntu 20.04 with build_essential, clang 18.0.0, Python 3.10.22 and notebook 7.0.4.

Reference
---------
https://github.com/jupyter/echo_kernel
https://saturncloud.io/blog/how-to-add-a-python-3-kernel-to-jupyter-ipython/
https://github.com/takluyver/bash_kernel
