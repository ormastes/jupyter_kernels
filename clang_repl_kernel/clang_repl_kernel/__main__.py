from ipykernel.kernelapp import IPKernelApp
from . import ClangReplKernel, install_bundles, ClangReplConfig
import sys

if __name__ == '__main__':
    # when parameter has '--install-default-toolchain' then install the default toolchain
    if '--install-default-toolchain' in sys.argv:
        install_bundles(ClangReplConfig.get_platform())
        sys.exit(0)
    IPKernelApp.launch_instance(kernel_class=ClangReplKernel)


