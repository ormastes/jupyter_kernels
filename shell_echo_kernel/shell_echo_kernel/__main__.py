from ipykernel.kernelapp import IPKernelApp
from . import ShellEchoKernel

IPKernelApp.launch_instance(kernel_class=ShellEchoKernel)