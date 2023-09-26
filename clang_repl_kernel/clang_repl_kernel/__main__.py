from ipykernel.kernelapp import IPKernelApp
from . import ClangReplKernel


if __name__ == '__main__':
    IPKernelApp.launch_instance(kernel_class=ClangReplKernel)


