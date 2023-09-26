import asyncio

from ipykernel.kernelbase import Kernel
import os
import subprocess
import errno
from enum import Enum
from subprocess import check_output

import subprocess
import os
import threading
import platform


def is_tool(name):
    try:
        devnull = open(os.devnull)
        subprocess.Popen([name], stdout=devnull, stderr=devnull).communicate()
    except OSError as e:
        if e.errno == errno.ENOENT:
            return False
    return True


def find_prog(prog):
    if os.path.isabs(prog):
        return prog
    if os.path.isfile(prog):
        return os.path.join(os.getcwd(), prog)

    if is_tool(prog):
        cmd = "where" if platform.system() == "Windows" else "which"
        out = check_output([cmd, prog])
        out = out.decode('utf-8')
        for line in out.splitlines():
            if len(line.strip()) > 0:
                out = line.strip()
                break
        assert os.path.isfile(out)
        return out
    return None


class ShellStatus(Enum):
    COMPLETE = 0
    CONTINUE = 1
    LOGGING = 2


class DefaultText:
    BIN_PATH_WIN = 'clang-repl.exe'
    BIN_PATH_LINUX = 'clang-repl'
    if os.name == 'nt':
        BIN_PATH = BIN_PATH_WIN
    else:
        BIN_PATH = BIN_PATH_LINUX
    BANNER_NAME = 'clang-repl'


class Shell:
    def __init__(self, bin_path='clang-repl', banner_name='clang-repl'):
        self.process = None
        self.bin_path = bin_path
        self.banner = banner_name + '> '
        self.banner_bytes = self.banner.encode('utf-8')
        self.banner_cont = banner_name + '... '
        self.banner_cont_bytes = self.banner_cont.encode('utf-8')
        self.env = os.environ.copy()
        self._prog = None
        self.loop = None

    def __del__(self):
        self.del_loop()

    async def _del_loop(self):
        if self.process is not None:
            self.process.stdin.close()
            await self.process.wait()

    def del_loop(self):
        if self.loop is not None:
            self.loop.run_until_complete(self._del_loop())
            self.loop.close()
            asyncio.set_event_loop(None)
            self.loop = None

    def prog(self):
        if self._prog is not None:
            return self._prog
        self._prog = find_prog(self.bin_path)
        if self._prog is None:
            raise Exception('Cannot find ' + self.bin_path)
        return self._prog

    def kill_and_run(self):
        self.del_loop()
        self.process.kill()
        self.run()

    async def _run(self, program):
        self.process = await asyncio.create_subprocess_exec(
            program=program,
            # args=[],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT, stdin=subprocess.PIPE)
        outs = ''
        read_size = len(self.banner)

        while self.process.returncode is None:
            stdout_data = await self.process.stdout.read(read_size)
            decoded = stdout_data.decode('utf-8')
            read_size = 1
            outs += decoded

            if self.check_endswith(outs, self.banner):
                break

    def run(self):
        program = self.prog()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            tasks = [asyncio.ensure_future(self._run(program))]
            self.loop.run_until_complete(asyncio.gather(*tasks))
        except RuntimeError as e:
            self.del_loop()
            raise e

    @staticmethod
    def check_endswith(text, end):
        if text.endswith('\r\n'):
            text = text[:-2]
        elif text.endswith('\n'):
            text = text[:-1]
        elif text.endswith('\r'):
            text = text[:-1]
        if text.endswith(end):
            return True
        text = text.strip()
        return text.endswith(end.strip())

    def handle_err(self):
        pass

    def check_input_err(self, command):
        if command.strip().endswith('\\'):
            self.handle_err()
            return True

        return False

    async def _do_execute(self, command, send_func):
        if self.check_input_err(command):
            return
        command_lines = []
        # '\' in each line except the last line
        lines = [line for line in command.splitlines() if len(line) > 0]
        for idx in range(len(lines) - 1):
            command_lines.append(lines[idx] + '\n')
        command_lines.append(lines[-1])
        command_lines[-1] += '\n'

        for idx in range(len(command_lines) - 1):
            cur_command = command_lines[idx]
            outs = bytearray()
            self.process.stdin.write(cur_command.encode('utf-8'))
            await self.process.stdin.drain()
            while self.process.returncode is None:
                stdoutdata = await self.process.stdout.read(1)
                outs += stdoutdata
                if not (outs == self.banner_cont_bytes[:len(outs)]):
                    self.handle_err()
                    return

                if outs[:len(self.banner_cont_bytes)] == self.banner_cont_bytes:
                    decoded = str(outs, 'utf-8')
                    decoded = decoded[:decoded.rfind(self.banner_cont)]
                    if len(decoded) > 0:
                        send_func(decoded)
                    break

        cur_command = command_lines[-1]
        outs = bytearray()
        self.process.stdin.write(cur_command.encode('utf-8'))
        await self.process.stdin.drain()
        # self.process.stdin.flush()
        last_newline = None
        while self.process.returncode is None:
            stdoutdata = await self.process.stdout.read(1)
            outs += stdoutdata
            if outs[:len(self.banner_bytes)] == self.banner_bytes:
                decoded = str(outs, 'utf-8')
                decoded = decoded[:decoded.rfind(self.banner)]
                if len(decoded) > 0:
                    send_func(decoded)
                break
            if outs[-1] == 0xA:  # == '\n'
                decoded = str(outs, 'utf-8')
                if last_newline is not None:
                    decoded = last_newline + decoded

                if decoded.endswith('\r\n'):
                    last_newline = '\r\n'
                    decoded = decoded[:-2]
                elif decoded.endswith('\n'):
                    last_newline = '\n'
                    decoded = decoded[:-1]
                else:
                    assert False

                if len(decoded) > 0:
                    send_func(decoded)
                outs = bytearray()

    def do_execute(self, command, send_func):
        try:
            self.loop.run_until_complete(self._do_execute(command, send_func))
        except RuntimeError as e:
            self.del_loop()
            raise e


class BashShell(Shell):
    def __init__(self, bin_path=DefaultText.BIN_PATH, banner_name=DefaultText.BANNER_NAME):
        super().__init__(bin_path, banner_name)


class WinShell(Shell):
    def __init__(self, bin_path=DefaultText.BIN_PATH, banner_name=DefaultText.BANNER_NAME):
        super().__init__(bin_path, banner_name)


class ShellEchoKernel(Kernel):
    ShellEchoKernel_InTest = False
    implementation = 'ShellEcho'
    implementation_version = '1.0'
    language = 'no-op'
    language_version = '0.1'
    language_info = {
        'name': 'shell_echo',
        'mimetype': 'text/plain',
        'file_extension': '.txt',
    }
    banner = "Shell Echo kernel - as useful as a parrot"


    def __init__(self, **kwargs):
        super().__init__(**kwargs)


        if os.name == 'nt':
            self.shell = WinShell()
        else:
            self.shell = BashShell()

        if not ShellEchoKernel.ShellEchoKernel_InTest:
            self.shell.run()

    def do_shutdown(self, restart):
        """Override in subclasses to do things when the frontend shuts down the
        kernel.
        """
        self.shell.kill_and_run()
        return {"status": "ok", "restart": restart}

    def do_execute(
            self,
            code,
            silent,
            store_history=True,
            user_expressions=None,
            allow_stdin=False,
            *,
            cell_id=None):
        def send_response(msg):
            stream_content = {'name': 'stdout', 'text': msg}
            self.send_response(self.iopub_socket, 'stream', stream_content)

        self.execution_count += 1
        self.shell.do_execute(code, send_response)

        return {
            'status': 'ok',
            # The base class increments the execution count
            'execution_count': self.execution_count,
            'payload': [],
            'user_expressions': {},
        }

    def do_clear(self):
        pass

    def do_apply(self, content, buffers, msg_id, reply_metadata):
        pass

    async def do_debug_request(self, msg):
        pass
