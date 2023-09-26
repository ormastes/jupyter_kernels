import os
from shell_echo_kernel import ShellEchoKernel, DefaultText
import pytest


def convert_result(result):
    if os.name == 'nt':
        return result.replace('\n', '\r\n')
    else:
        return result


@pytest.fixture
def setup_dir():
    if not os.path.isfile('clang-repl.cpp'):
        os.chdir('..')


@pytest.fixture
def kernel():
    ShellEchoKernel.ShellEchoKernel_InTest = True
    result = MockedKernel()
    result.shell._prog = DefaultText.BIN_PATH
    result.shell.run()
    return result


class MockedKernel(ShellEchoKernel):
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
    result = os.path.isfile(DefaultText.BIN_PATH)
    assert result


def test_new(setup_dir):
    # Create an instance of the kernel
    ShellEchoKernel.ShellEchoKernel_InTest = True
    kernel = MockedKernel()
    kernel.shell._prog = DefaultText.BIN_PATH
    kernel.shell.run()
    assert kernel.execution_count == 0
    assert kernel.stream is None
    assert kernel.msg_or_type is None
    assert kernel.content is None


def test_hello(setup_dir, kernel):
    # Run the kernel
    kernel.do_execute('hello', False)
    assert kernel.execution_count == 1
    assert kernel.stream == kernel.iopub_socket
    assert kernel.msg_or_type == 'stream'
    assert kernel.content == {'name': 'stdout', 'text': 'hello'}


def test_hello_two_line(setup_dir, kernel):
    # Run the kernel
    kernel.do_execute('hello\\\nworld\n', False)
    assert kernel.execution_count == 1
    assert kernel.stream == kernel.iopub_socket
    assert kernel.msg_or_type == 'stream'
    result = '\nworld'
    assert kernel.content == {'name': 'stdout', 'text': convert_result(result)}


def test_hello_three_line(setup_dir, kernel):
    # Run the kernel
    kernel.do_execute('hello\\\nworld\\\n!\n', False)
    assert kernel.execution_count == 1
    assert kernel.stream == kernel.iopub_socket
    assert kernel.msg_or_type == 'stream'
    assert kernel.content == {'name': 'stdout', 'text': convert_result('\n!')}


def test_hello_three_line_no_newline(setup_dir, kernel):
    # Run the kernel
    kernel.do_execute('hello\\\nworld\\\n!', False)
    assert kernel.execution_count == 1
    assert kernel.stream == kernel.iopub_socket
    assert kernel.msg_or_type == 'stream'
    assert kernel.content == {'name': 'stdout', 'text': convert_result('\n!')}


def test_hello_three_line_multiple_newline(setup_dir, kernel):
    # Run the kernel
    kernel.do_execute('hello\\\n\\\nworld\\\n\\\n!\n', False)
    assert kernel.execution_count == 1
    assert kernel.stream == kernel.iopub_socket
    assert kernel.msg_or_type == 'stream'
    assert kernel.content == {'name': 'stdout', 'text': convert_result('\n!')}
