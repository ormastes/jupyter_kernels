from ipykernel.kernelapp import IPKernelApp
from kernel import ClangReplKernel, ClangReplConfig
from install import install_bundles
import sys

if __name__ == '__main__':
    # when parameter has '--install-default-toolchain' then install the default toolchain
    if '--install-default-toolchain' in sys.argv:
        install_bundles(ClangReplConfig.platform())
        sys.exit(0)
    if '--interactive' in sys.argv:
        ClangReplKernel.interactive = True
        kernel = ClangReplKernel()
        # take input from user and call do_execute if it is not exit(...)
        def send_response(msg):
            print(msg)
        while True:
            try:
                sys.stdout.write(">>> ")
                sys.stdout.flush()  # ensure the prompt is printed immediately
                code = sys.stdin.readline().rstrip("\n")
                while code.endswith('\\'):
                    sys.stdout.write("... ")
                    new_code = sys.stdin.readline().rstrip("\n")
                    code = code[:-1] + new_code
                if code.strip() == 'exit()':
                    break
                kernel.do_execute(code, False, custom_send_response=send_response)
            except EOFError:
                break
        sys.exit(0)
    IPKernelApp.launch_instance(kernel_class=ClangReplKernel)


