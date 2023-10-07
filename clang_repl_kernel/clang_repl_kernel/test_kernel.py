import os
import platform

from clang_repl_kernel import ClangReplKernel, ClangReplConfig, install_bundles
import pytest


def convert_result(result):
    if os.name == 'nt':
        return result.replace('\n', '\r\n')
    else:
        return result


@pytest.fixture
def setup_dir():
    # set env export CPLUS_INCLUDE_PATH=/mnt/c/cling/jupyter/llvm-project_linux/build/lib/clang/18/include
    env = os.environ
    env['CPLUS_INCLUDE_PATH'] = '/mnt/c/cling/jupyter/llvm-project_linux/build/lib/clang/18/include'

    if not os.path.isdir(platform.system()):
        pass #raise Exception('Please run this test on supported platform.')


@pytest.fixture
def kernel():
    ClangReplKernel.ClangReplKernel_InTest = True
    result = MockedKernel()
    result.my_shell._prog = ClangReplConfig.BIN_PATH
    result.my_shell.run()
    return result


class MockedKernel(ClangReplKernel):
    def __init__(self):
        super().__init__()
        self.stream = None
        self.msg_or_type = None
        self.content = None

    def send_response(
            self,
            stream,
            msg_or_type,
            content=None,
            ident=None,
            buffers=None,
            track=False,
            header=None,
            metadata=None,
            channel=None):
        self.stream = stream
        self.msg_or_type = msg_or_type
        self.content = content


def test_env_dir(setup_dir):
    # clang-repl file exist on current directory
    result = os.path.isfile(ClangReplConfig.BIN_PATH)
    assert result


def test_install_bundles():
    # delete bundle if exist
    assert False
    if os.path.exists(ClangReplConfig.BIN_PATH):
        os.remove(ClangReplConfig.BIN_PATH)
    install_bundles()
    assert os.path.exists(ClangReplConfig.BIN_PATH)


def test_new(setup_dir):
    # Create an instance of the kernel
    ClangReplKernel.ClangReplKernel_InTest = True
    kernel = MockedKernel()
    kernel.my_shell._prog = ClangReplConfig.BIN_PATH
    kernel.my_shell.run()
    assert kernel.execution_count == 0
    assert kernel.stream is None
    assert kernel.msg_or_type is None
    assert kernel.content is None


def test_hello(setup_dir, kernel):
    # Run the kernel
    kernel.do_execute('#include<cstdio>\nprintf("hello, world");\n', False)
    # assert kernel.execution_count == 1
    assert kernel.stream == kernel.iopub_socket
    assert kernel.msg_or_type == 'stream'
    assert kernel.content == {'name': 'stdout', 'text': 'hello, world'}


def test_version(setup_dir, kernel):
    # Run the kernel
    kernel.do_execute('#include<cstdio>\nprintf("%ld", __cplusplus);\n', False)
    # assert kernel.execution_count == 1
    assert kernel.stream == kernel.iopub_socket
    assert kernel.msg_or_type == 'stream'
    assert kernel.content == {'name': 'stdout', 'text': 'hello, world'}


def test_hello_two_line(setup_dir, kernel):
    # Run the kernel
    kernel.do_execute('#include<cstdio>\nprintf("hello\\n");\nprintf("world\\n");\n', False)
    # assert kernel.execution_count == 1
    assert kernel.stream == kernel.iopub_socket
    assert kernel.msg_or_type == 'stream'
    assert kernel.content == {'name': 'stdout', 'text': '\nworld'}


def test_hello_three_line(setup_dir, kernel):
    # Run the kernel
    kernel.do_execute('#include<cstdio>\nprintf("hello\\n");\nprintf("world\\n");\nprintf("!\\n");\n', False)
    # assert kernel.execution_count == 1
    assert kernel.stream == kernel.iopub_socket
    assert kernel.msg_or_type == 'stream'
    assert kernel.content == {'name': 'stdout', 'text': '\n!'}


def test_hello_three_line_no_newline(setup_dir):
    # Create an instance of the kernel
    kernel = MockedKernel()
    # Run the kernel
    kernel.do_execute('#include<cstdio>\nprintf("hello\\n");\nprintf("world\\n");\nprintf("!\\n");', False)
    # assert kernel.execution_count == 1
    assert kernel.stream == kernel.iopub_socket
    assert kernel.msg_or_type == 'stream'
    assert kernel.content == {'name': 'stdout', 'text': '\n!'}


def test_hello_three_line_multiple_newline(setup_dir):
    # Create an instance of the kernel
    kernel = MockedKernel()
    # Run the kernel
    kernel.do_execute('#include<cstdio>\nprintf("hello\\n");\nprintf("world\\n");\n\nprintf("!\\n");\n', False)
    # assert kernel.execution_count == 1
    assert kernel.stream == kernel.iopub_socket
    assert kernel.msg_or_type == 'stream'
    assert kernel.content == {'name': 'stdout', 'text': '\n!'}
