import asyncio
from ipykernel.kernelbase import Kernel
import errno
from enum import Enum
from subprocess import check_output
import subprocess
import os
import sys
import platform
import logging
from . import is_done
import time

CLANG_REPL_DEBUG = True

LINUX_WORKAROUND = """class printf_streambuf : public std::streambuf {\
private:\
    static const int bufferSize = 256;\
    char buffer[bufferSize];\
public:\
    printf_streambuf() {\
        setp(buffer, buffer + bufferSize - 1);\
    }\
protected:\
    virtual int overflow(int c) override {\
        if (c != EOF) {\
            *pptr() = c;\
            pbump(1);\
        }\
        if (flushBuffer() == EOF)\
            return EOF;\
        return c;\
    }\
    virtual int sync() override {\
        return flushBuffer();\
    }\
private:\
    int flushBuffer() {\
        int num = int(pptr() - pbase());\
        if (num > 0) {\
            buffer[num] = '\\0';\
            if (std::printf("%s", buffer) < 0)\
                return EOF;\
            setp(buffer, buffer + bufferSize - 1);\
        }\
        return 0;\
    }\
};
class printf_ostream : public std::basic_ostream<char> {\
private:\
    printf_streambuf psb;\
public:\
    printf_ostream() : std::basic_ostream<char>(&psb) {}\
};
printf_ostream pcout;
pcout << std::unitbuf;
"""
WINDOW_WORKAROUND = """"""
MACOS_WORKAROUND = """"""
workarounds = [LINUX_WORKAROUND, WINDOW_WORKAROUND, MACOS_WORKAROUND]


def update_platform_system(platform_system):
    if platform_system == 'Windows':
        platform_system = 'WinMG64'
    elif platform_system == 'Linux':
        platform_system = 'Lin64'
    return platform_system


def is_tool(name):
    try:
        import subprocess, os
        my_env = os.environ.copy()
        devnull = open(os.devnull)
        subprocess.Popen([name], stdout=devnull, stderr=devnull, env=my_env).communicate()
    except OSError as e:
        if e.errno == errno.ENOENT:
            return False
    return True


def find_prog(prog):
    if os.path.isabs(prog) and os.path.exists(prog):
        return prog, False
    # file part of prog
    prog = os.path.basename(prog)

    os_dir = None
    if platform.system() == "Windows":
        # find first directory start with 'Win'
        for dir in os.listdir(ClangReplConfig.CLANG_BASE_DIR):
            if dir.startswith('Win') and os.path.isdir(os.path.join(ClangReplConfig.CLANG_BASE_DIR, dir)):
                os_dir = dir
                break
    else:
        os_dir = update_platform_system(platform.system())

    if os_dir is not None:
        embedded_prog = os.path.join(ClangReplConfig.CLANG_BASE_DIR, os_dir, "bin", prog)
        if os.path.isfile(embedded_prog) and os.path.exists(embedded_prog):
            return embedded_prog, False

    if is_tool(prog):
        cmd = "where" if platform.system() == "Windows" else "which"
        out = check_output([cmd, prog])
        out = out.decode('utf-8')
        for line in out.splitlines():
            if len(line.strip()) > 0:
                out = line.strip()
                break
        assert os.path.isfile(out)
        assert os.path.exists(out)
        return out, True
    return None, False


class ShellStatus(Enum):
    COMPLETE = 0
    CONTINUE = 1
    LOGGING = 2


class PlatformPath:
    class Platform(Enum):
        Linux = 0
        Windows = 1
        MacOS = 2

    class BIT(Enum):
        BIT64 = 0
        BIT32 = 1

    INSTALL_PATH = [
        ['Lin64', 'Lin32'],
        ['WinMG64', 'WinMG32'],
        ['App64', 'App32']
    ]

    PYTHON_DLL_PATH = [
        ['Lin64', 'Lin32'],
        ['Win64', 'Win32'],
        ['App64', 'App32']
    ]

    PATH = [
        ['x86_64-linux-gnu', 'i686-linux-gnu', ],
        ['x86_64-w64-mingw32', 'i686-w64-mingw32'],
        ['x86_64-apple-darwin', 'i686-apple-darwin']
    ]


class ClangReplConfig:
    DLIB = ['libc++.so', 'libunwind.so']  # 'libclang.so', 'libc.so','libpthread.so'
    USER_DEFINED_BIN_PATH = None
    USER_DEFINED_INSTALL_PATH = None
    INSTALL_CLANG_CONFIG_FILE_NAME = 'installed_clang.txt'
    PYTHON_CLANG_LIB = 'libclang.so'
    HEADERS = ['iostream', 'cstdio', 'streambuf']
    BIN = 'clang-repl'
    BIN_CLANG = 'clang'
    PYTHON_EXE = 'python3'
    DYLIB_PATH_ENV = 'LD_LIBRARY_PATH'
    PLATFORM_NAME_ENUM = PlatformPath.Platform.Linux
    if platform.system() == 'Windows':
        DLIB = ['libclang-cpp.dll', 'ucrtbase.dll', 'msvcrt.dll', 'libc++.dll', 'libunwind.dll', 'libwinpthread-1.dll']
        PYTHON_CLANG_LIB = 'libclang.dll'
        BIN = 'clang-repl.exe'
        BIN_CLANG = 'clang.exe'
        PYTHON_EXE = 'python.exe'
        SCRIPT_EXT = '.bat'
        DYLIB_PATH_ENV = 'PATH'
        PLATFORM_NAME_ENUM = PlatformPath.Platform.Windows
    elif platform.system() == 'Darwin':
        DLIB = ['libclang.dylib', 'libc.dylib', 'libstdc++.dylib', 'libunwind.dylib', 'libpthread.dylib']
        PYTHON_CLANG_LIB = 'libclang.dylib'
        DYLIB_PATH_ENV = 'DYLD_LIBRARY_PATH'
        PLATFORM_NAME_ENUM = PlatformPath.Platform.MacOS
    else:
        pass
    CLANG_BASE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'clang')
    if not os.path.exists(CLANG_BASE_DIR):
        os.makedirs(CLANG_BASE_DIR)
    PYTHON_CLANG_DLL_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'dll')
    BANNER_NAME = 'clang-repl'
    PREFER_BUNDLE = True  # if platform.system() == 'Windows' else False
    # BIN_DIR = os.path.join(CLANG_BASE_DIR, platform.system())
    # BIN_PATH = os.path.join(BIN_DIR, BIN)
    _platform = None
    PLATFORM_BIT = None

    @staticmethod
    def get_install_clang_config_file():
        return os.path.join(ClangReplConfig.CLANG_BASE_DIR, ClangReplConfig.INSTALL_CLANG_CONFIG_FILE_NAME)

    @staticmethod
    def platform():
        return ClangReplConfig._platform

    @staticmethod
    def set_platform(platform):
        ClangReplConfig._platform = platform
        if ("32" in platform):
            ClangReplConfig.PLATFORM_BIT = PlatformPath.BIT.BIT32
        else:
            ClangReplConfig.PLATFORM_BIT = PlatformPath.BIT.BIT64

    @staticmethod
    def set_user_defined_bin_path(bin_path):
        # remove rightmost '//' or '\\' if exists
        if bin_path.endswith('/') or bin_path.endswith('\\'):
            bin_path = bin_path[:-1]
        ClangReplConfig.USER_DEFINED_BIN_PATH = bin_path
        ClangReplConfig.USER_DEFINED_INSTALL_PATH = os.path.dirname(bin_path)

    @staticmethod
    def get_platform_path():
        return PlatformPath.PATH[ClangReplConfig.PLATFORM_NAME_ENUM.value][ClangReplConfig.PLATFORM_BIT.value]

    @staticmethod
    def get_install_dir():
        if ClangReplConfig.USER_DEFINED_INSTALL_PATH is not None:
            return ClangReplConfig.USER_DEFINED_INSTALL_PATH
        else:
            return os.path.join(ClangReplConfig.CLANG_BASE_DIR, ClangReplConfig.platform())

    @staticmethod
    def get_bin_dir():
        if ClangReplConfig.USER_DEFINED_BIN_PATH is not None:
            return ClangReplConfig.USER_DEFINED_BIN_PATH
        else:
            return os.path.join(ClangReplConfig.get_install_dir(), 'bin')

    @staticmethod
    def get_c_include():
        if ClangReplConfig.USER_DEFINED_BIN_PATH is not None:
            return os.path.join(ClangReplConfig.USER_DEFINED_BIN_PATH, '..', ClangReplConfig.get_platform_path(),
                                'include')
        else:
            return os.path.join(ClangReplConfig.get_install_dir(), ClangReplConfig.get_platform_path(), 'include')

    @staticmethod
    def get_cpp_include():
        if ClangReplConfig.USER_DEFINED_BIN_PATH is not None:
            return os.path.join(ClangReplConfig.USER_DEFINED_BIN_PATH, '..', ClangReplConfig.get_platform_path(),
                                'include', 'c++', 'v1')
        else:
            return os.path.join(ClangReplConfig.get_install_dir(), ClangReplConfig.get_platform_path(),
                                'include', 'c++', 'v1')

    @staticmethod
    def get_bin_path():
        return os.path.join(ClangReplConfig.get_bin_dir(), ClangReplConfig.BIN)

    @staticmethod
    def get_dynlib_dir():
        bin_dir = ClangReplConfig.get_bin_dir()
        assert ClangReplConfig.PLATFORM_BIT is not None
        sub_bin_dir = bin_dir + "/../" + PlatformPath.PATH[ClangReplConfig.PLATFORM_NAME_ENUM.value][
            ClangReplConfig.PLATFORM_BIT.value] + '/lib'
        abs_path = []
        # when linux
        if ClangReplConfig.PLATFORM_NAME_ENUM == PlatformPath.Platform.Linux:
            abs_path.append(
                os.path.join('/lib',
                             PlatformPath.PATH[ClangReplConfig.PLATFORM_NAME_ENUM.value][
                                 ClangReplConfig.PLATFORM_BIT.value]))
            abs_path.append(os.path.abspath(ClangReplConfig.PYTHON_CLANG_DLL_DIR))

        abs_path.append(os.path.abspath(bin_dir))
        abs_path.append(os.path.abspath(sub_bin_dir))

        return abs_path

    @classmethod
    def get_available_bin_path(cls):
        bin_path = []
        for a_dir in os.listdir(ClangReplConfig.CLANG_BASE_DIR):
            a_dir_pullpath = os.path.join(ClangReplConfig.CLANG_BASE_DIR, a_dir)
            if os.path.isdir(a_dir_pullpath) and is_done(a_dir_pullpath):
                bin_path.append(a_dir)
        return bin_path

    @staticmethod
    def get_python_bits():
        bits, _ = platform.architecture()
        if bits == '32bit':
            return PlatformPath.BIT.BIT32
        return PlatformPath.BIT.BIT64

    @staticmethod
    def _get_default_platform():
        if ClangReplConfig.USER_DEFINED_BIN_PATH is not None:
            return ClangReplConfig.USER_DEFINED_BIN_PATH

        platformdirs = PlatformPath.PATH[ClangReplConfig.PLATFORM_NAME_ENUM.value]
        if len(ClangReplConfig.get_available_bin_path()) == 0:
            import platform
            bits, _ = platform.architecture()
            if bits == '32bit':
                return platformdirs[PlatformPath.BIT.BIT32.value]
            return platformdirs[PlatformPath.BIT.BIT64.value]

        for bin_path in ClangReplConfig.get_available_bin_path():
            if platformdirs[PlatformPath.BIT.BIT64.value] in bin_path:
                return bin_path
            if platformdirs[PlatformPath.BIT.BIT32.value] in bin_path:
                return bin_path

        return ClangReplConfig.get_available_bin_path()[0]

    @staticmethod
    def get_default_platform():
        # index of the platform
        bin_path_platform = ClangReplConfig._get_default_platform()
        for platformIdx in PlatformPath.Platform:
            for bitIdx in PlatformPath.BIT:
                if PlatformPath.PATH[platformIdx.value][bitIdx.value] in bin_path_platform:
                    return PlatformPath.INSTALL_PATH[platformIdx.value][bitIdx.value]
        return bin_path_platform


class Shell:
    env = os.environ.copy()

    def __init__(self, bin_path, banner_name='clang-repl'):
        self.process = None
        self.bin_path = bin_path
        self.binary = None
        self.banner = banner_name + '> '
        self.banner_bytes = self.banner.encode('utf-8')
        self.banner_cont = banner_name + '...   '
        self.banner_cont_bytes = self.banner_cont.encode('utf-8')
        self.env = Shell.env
        self.tool_found = None
        self._prog = None
        self.loop = None
        self.args = []
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        self.logger = logging.getLogger('LOGGER_NAME')

    def __del__(self):
        self.del_loop()

    @staticmethod
    def get_available_bin_path():
        # get directory under ClangReplConfig.CLANG_BASE_DIR
        bin_path = []
        for a_dir in os.listdir(ClangReplConfig.CLANG_BASE_DIR):
            if os.path.isdir(os.path.join(ClangReplConfig.CLANG_BASE_DIR, a_dir)):
                bin_path.append(a_dir)
        return bin_path

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
            return self._prog, self.tool_found
        self._prog, self.tool_found = find_prog(self.binary)
        if self._prog is None:
            raise Exception('Cannot find ' + self.binary)
        return self._prog, self.tool_found

    def kill_and_run(self):
        self.del_loop()
        self.process.kill()
        self.run()

    def _run(self, program, tool_found):
        if not os.path.exists(program):
            raise Exception('Cannot find: ' + program + " in " + os.getcwd() +
                            " in src dir: " + os.path.dirname(os.path.realpath(__file__)))

        program_with_args = [program] + self.args
        env = self.env
        program_path = str(os.path.dirname(program)) + os.pathsep + os.getcwd() + os.pathsep
        if env['PATH'] is not None and not env['PATH'].startswith(program_path):
            env['PATH'] = program_path + env['PATH']
        # for key in env:
        # logger.debug('This is hidden')
        # logger.warning('This too')
        # self.logger.info(key + " = " + env[key])
        program_with_args = " ".join(program_with_args)
        self.process = subprocess.Popen(
            program_with_args,
            # args=[],
            # text=True,
            # bufsize=1,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, stdin=subprocess.PIPE, env=env)
        outs = ''
        read_size = len(self.banner)
        while self.process.returncode is None:
            stdout_data = self.process.stdout.read(read_size)
            decoded = stdout_data.decode('utf-8')
            read_size = 1
            outs += decoded
            if self.check_endswith(outs, self.banner):
                break

        def _silent_response(msg):
            pass

        for dylib in ClangReplConfig.DLIB:
            self.do_execute('%lib ' + dylib + '\n', _silent_response)
            assert self.process.returncode is None

        for header in ClangReplConfig.HEADERS:
            self.do_execute('#include <' + header + '>\n', _silent_response)
            assert self.process.returncode is None

        accumulated_line = ""
        for line in workarounds[ClangReplConfig.PLATFORM_NAME_ENUM.value].splitlines():
            if line.endswith('\\'):
                accumulated_line += line[:-1]
                continue
            else:
                accumulated_line += line
            self.do_execute(accumulated_line, _silent_response)
            accumulated_line = ""
            assert self.process.returncode is None

    def run(self):
        program, tool_found = self.prog()
        return self._run(program, tool_found)

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

    def _do_execute(self, command, send_func):
        if CLANG_REPL_DEBUG:
            print("Command: ", command)
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
            cur_command_strip = cur_command.encode('utf-8').strip()
            if cur_command_strip.startswith(b'#'):
                if cur_command_strip.endswith(b'\\'):
                    cur_command = cur_command_strip[:-1] + '\n'
            elif not cur_command_strip.endswith(b'\\'):
                cur_command = cur_command.rstrip() + '\\\n'
            outs = bytearray()
            self.process.stdin.write(cur_command.encode('utf-8'))
            self.process.stdin.flush()

            while self.process.returncode is None:
                stdout_data = self.process.stdout.read(1)
                outs += stdout_data
                if CLANG_REPL_DEBUG:
                    print("outs: ", outs, ", stdout_data: ", stdout_data)
                if len(stdout_data) == 0:
                    out, err = self.process.communicate()
                    print("End of process, out: ", out, ", error code: ", err)
                    return
                if not (outs == self.banner_cont_bytes[:len(outs)]) and not (outs == self.banner_bytes[:len(outs)]):
                    self.handle_err()
                    return
                if len(outs) >= len(self.banner_bytes):
                    banner_part = outs[len(outs) - len(self.banner_bytes):]
                    if banner_part == self.banner_bytes:
                        decoded = str(outs, 'utf-8')
                        decoded = decoded[:decoded.rfind(self.banner)]
                        if len(decoded) > 0:
                            send_func(decoded)
                        break
                if len(outs) >= len(self.banner_cont_bytes):
                    banner_part = outs[len(outs) - len(self.banner_cont_bytes):]
                    if banner_part == self.banner_cont_bytes:
                        decoded = str(outs, 'utf-8')
                        decoded = decoded[:decoded.rfind(self.banner_cont)]
                        if len(decoded) > 0:
                            send_func(decoded)
                        break

        cur_command = command_lines[-1]
        if cur_command.rstrip().endswith('\\'):
            cur_command = cur_command.rstrip()[:-1] + '\n'
        outs = bytearray()
        self.process.stdin.write(cur_command.encode('utf-8'))
        self.process.stdin.flush()
        last_newline = None
        while self.process.returncode is None:
            stdout_data = self.process.stdout.read(1)
            outs += stdout_data
            if CLANG_REPL_DEBUG:
                print("outs: ", outs, ", stdout_data: ", stdout_data)
            if len(stdout_data) == 0:
                out, err = self.process.communicate()
                print("End of process, out: ", out, ", error code: ", err)
                return
            if len(outs) >= len(self.banner_bytes):
                banner_part = outs[len(outs) - len(self.banner_bytes):]
                if banner_part == self.banner_bytes:
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

        return self._do_execute(command, send_func)

    def do_execute_sync(self, command):
        response_message = []

        def _send_response(msg):
            response_message.append(msg)

        import threading
        _kernel_thread = threading.Thread(target=self.do_execute, args=[command, _send_response], daemon=True)
        _kernel_thread.start()

        _kernel_thread.join()
        full_message = ''.join(response_message)
        return full_message


class BashShell(Shell):
    def __init__(self, bin_path, banner_name=ClangReplConfig.BANNER_NAME):
        super().__init__(bin_path, banner_name)
        self.binary = 'clang-repl'


class WinShell(Shell):
    def __init__(self, bin_path, banner_name=ClangReplConfig.BANNER_NAME):
        super().__init__(bin_path, banner_name)
        self.binary = 'clang-repl.exe'


class ClangReplKernel(Kernel):
    ClangReplKernel_InTest = False
    implementation = 'ClangRepl'
    implementation_version = '1.0'
    language = 'no-op'
    language_version = '0.1'
    language_info = {
        'name': 'c++',
        'codemirror_mode': 'c++',
        'mimetype': 'text/x-c++src',
        'file_extension': '.cpp',
    }
    # it does not work and make conflict with other kernel instances.
    # std = CaselessStrEnum(default_value='c++23',
    #                      values=['c++14', 'c++17', 'c++20', 'c++23'],
    #                      help="C++ standard to use, either c++14, c++17, c++20 or c++23").tag(config=True)

    banner = "Clang Repl kernel - clang repl interpreter for jupyter"

    inputs = []

    @staticmethod
    def arg_inputs(an_input):
        ClangReplKernel.inputs.append(an_input)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if os.path.exists(ClangReplConfig.get_install_clang_config_file()):
            with open(ClangReplConfig.get_install_clang_config_file(), 'r') as f:
                ClangReplConfig.set_user_defined_bin_path(f.read().strip())
        else:
            platforms = ClangReplConfig.get_available_bin_path()
            if len(platforms) == 0:
                raise Exception('Cannot find any installed clang for this platform')

        ClangReplConfig.set_platform(ClangReplConfig.get_default_platform())

        if os.name == 'nt':
            self.my_shell = WinShell(ClangReplConfig.platform())
        else:
            self.my_shell = BashShell(ClangReplConfig.platform())

        self.std_arg = 'c++23'
        for an_input in reversed(sys.argv):
            if an_input.startswith('--std='):
                self.std_arg = an_input[6:]
                break
        self.my_shell.args = ['--Xcc=-std=' + self.std_arg]

        for dy_libpath in ClangReplConfig.get_dynlib_dir():
            if not ClangReplConfig.DYLIB_PATH_ENV in self.my_shell.env:
                self.my_shell.env[ClangReplConfig.DYLIB_PATH_ENV] = ""
            self.my_shell.env[ClangReplConfig.DYLIB_PATH_ENV] = dy_libpath + os.pathsep + self.my_shell.env[
                ClangReplConfig.DYLIB_PATH_ENV]

        self.my_shell.env["CPATH"] = os.pathsep.join(
            filter(None, [self.my_shell.env.get("CPATH", ""), ClangReplConfig.get_c_include()])
        )
        self.my_shell.env["CPLUS_INCLUDE_PATH"] = os.pathsep.join(
            filter(None, [self.my_shell.env.get("CPLUS_INCLUDE_PATH", ""), ClangReplConfig.get_cpp_include()])
        )
        if not ClangReplKernel.ClangReplKernel_InTest:
            self.my_shell.run()

    def do_shutdown(self, restart):
        """Override in subclasses to do things when the frontend shuts down the
        kernel.
        """
        self.my_shell.kill_and_run()
        return {"status": "ok", "restart": restart}

    def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False, *, cell_id=None,
                   custom_send_response=None,
                   **kwargs):
        def _send_response(msg):
            stream_content = {'name': 'stdout', 'text': msg}
            self.send_response(self.iopub_socket, 'stream', stream_content)

        send_response = custom_send_response if custom_send_response is not None else _send_response

        if code.strip().startswith('%<<'):
            code = code.strip()[3:]
            code = code[:-1] if code.endswith(';') else code
            code = "std::cout << " + code + " << std::endl;"
        if ClangReplConfig.PLATFORM_NAME_ENUM == PlatformPath.Platform.Linux:
            code.replace("std::cout", "pcout")
        # self.execution_count += 1
        self.my_shell.do_execute(code, send_response)

        return {
            'status': 'ok',
            # The base class increments the execution count
            'execution_count': self.execution_count,
            'payload': [],
            'user_expressions': {},
        }

    def do_execute_sync(self, code):

        if code.strip().startswith('%<<'):
            code = code.strip()[3:]
            code = code[:-1] if code.endswith(';') else code
            code = "std::cout << " + code + " << std::endl;"
        if ClangReplConfig.PLATFORM_NAME_ENUM == PlatformPath.Platform.Linux:
            code.replace("std::cout", "pcout")
        # self.execution_count += 1
        output = self.my_shell.do_execute_sync(code)

        return {
            'status': 'ok',
            # The base class increments the execution count
            'execution_count': self.execution_count,
            'payload': [],
            'user_expressions': {},
            'output': output
        }

    def do_clear(self):
        pass

    def do_apply(self, content, buffers, msg_id, reply_metadata):
        pass

    async def do_debug_request(self, msg):
        pass
