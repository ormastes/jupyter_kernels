from ipykernel.kernelapp import IPKernelApp
from . import MyEchoKernel

IPKernelApp.launch_instance(kernel_class=MyEchoKernel)