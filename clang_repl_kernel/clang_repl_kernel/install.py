import argparse
import json
import os
import re
import subprocess
import sys
import shutil
import urllib

import requests
import platform
import zipfile

from jupyter_client.kernelspec import KernelSpecManager
from tempfile import TemporaryDirectory
from clang_repl_kernel import ClangReplConfig, download

kernel_json = {
    "argv": [ClangReplConfig.PYTHON_EXE, "-m", "clang_repl_kernel", "-f", "{connection_file}"],
    "display_name": "Clang-Repl",
    "language": "c++",
    "env": {"CPLUS_INCLUDE_PATH":""}
}


def install_my_kernel_spec(user=True, prefix=None, args=None, suffix=None, name_suffix='',
                           platform_system=platform.system(), installed_clang_executable=None):
    with TemporaryDirectory() as td:
        # if os support chmod
        if hasattr(os, 'chmod'):
            os.chmod(td, 0o755)  # Starts off as 700, not user readable
        local_kernel_json = kernel_json.copy()
        local_kernel_json['argv'].extend(args)
        local_kernel_json['display_name'] += name_suffix
        my_env = os.environ.copy()
        for key in my_env:
            local_kernel_json['env'][key] = my_env[key]
            print(key + " = " + my_env[key])
        if len(my_env) == 0:
            print("No environment variables found. Please set CPLUS_INCLUDE_PATH manually")
            local_kernel_json['env']['EMPTY'] = 'True'

        with open(os.path.join(td, 'kernel.json'), 'w') as f:
            json.dump(local_kernel_json, f, sort_keys=True)
        print('Installing Jupyter kernel spec')
        # requires logo files in kernel root directory
        cur_path = os.path.dirname(os.path.realpath(__file__))
        for logo in ["logo_32X32.png", "logo_64X64.png"]:
            try:
                shutil.copy(os.path.join(cur_path, logo), td)
            except FileNotFoundError:
                print("Custom logo files not found. Default logos will be used.")

        clang_repl_file = 'clang_repl' + suffix

        install_bundles(platform_system, installed_clang_executable)

        KernelSpecManager().install_kernel_spec(td, clang_repl_file, user=user, prefix=prefix)


def get_filename_from_response(url):
    response = requests.head(url, allow_redirects=True)

    # 1. Check if Content-Disposition is provided
    content_disp = response.headers.get("Content-Disposition")
    if content_disp:
        # Attempt to extract filename="..." from Content-Disposition
        match = re.search(r'filename="([^"]+)"', content_disp)
        if match:
            return match.group(1)

    return "downloaded.file"

def install_bundles(platform_system, installed_clang_executable):

    if platform_system == 'Windows':
        platform_system = 'WinMG64'
    elif platform_system == 'Linux':
        platform_system = 'Lin64'

    if platform_system is None:
        ClangReplConfig.set_platform(ClangReplConfig.get_default_platform())
    else:
        ClangReplConfig.set_platform(platform_system)

    if installed_clang_executable is not None:
        r_idx = installed_clang_executable.rfind('clang-repl')
        clang_repl_dir = installed_clang_executable[:r_idx]
        ClangReplConfig.set_user_defined_bin_path(clang_repl_dir)
        if not os.path.exists(ClangReplConfig.CLANG_BASE_DIR):
            os.makedirs(ClangReplConfig.CLANG_BASE_DIR)
        installed_clang_config_file = ClangReplConfig.get_install_clang_config_file()
        # write clang_repl_dir on installed_clang.txt. delete the file if it already exists
        if os.path.exists(installed_clang_config_file):
            os.remove(installed_clang_config_file)
        with open(installed_clang_config_file, 'w') as f:
            f.write(clang_repl_dir)

        return

    if os.path.exists(ClangReplConfig.get_install_clang_config_file()):
        return

    if not os.path.exists(ClangReplConfig.get_bin_path()):
        zip_filename = platform_system+".zip"
        extract_dir = ClangReplConfig.get_install_dir()
        download(zip_filename, extract_dir)


def _is_root():
    try:
        return os.geteuid() == 0
    except AttributeError:
        return False  # assume not an admin on non-Unix platforms


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--user', action='store_true',
                    help="Install to the per-user kernels registry. Default if not root.")
    ap.add_argument('--sys-prefix', action='store_true',
                    help="Install to sys.prefix (e.g. a virtualenv or conda env)")
    ap.add_argument('--prefix',
                    help="Install to the given prefix. "
                         "Kernelspec will be installed in {PREFIX}/share/jupyter/kernels/")
    ap.add_argument('--platform-system',
                    help="Platform system (Linux, Windows, Lin64, WinMG64, Lin32, WinMG32)",
                    default=platform.system())
    ap.add_argument('--installed-clang-executable',
                    help="Installed clang executable path (Can not be used with --platform-system)")
    args = ap.parse_args(argv)

    if args.sys_prefix:
        args.prefix = sys.prefix
    if not args.prefix and not _is_root():
        args.user = True

    install_my_kernel_spec(user=args.user, prefix=args.prefix,
                           args=['--std=c++14'], suffix='_cpp14', name_suffix=' (C++14)', platform_system=args.platform_system, installed_clang_executable=args.installed_clang_executable)
    install_my_kernel_spec(user=args.user, prefix=args.prefix,
                           args=['--std=c++17'], suffix='_cpp17', name_suffix=' (C++17)', platform_system=args.platform_system, installed_clang_executable=args.installed_clang_executable)
    install_my_kernel_spec(user=args.user, prefix=args.prefix,
                           args=['--std=c++20'], suffix='_cpp20', name_suffix=' (C++20)', platform_system=args.platform_system, installed_clang_executable=args.installed_clang_executable)
    install_my_kernel_spec(user=args.user, prefix=args.prefix,
                           args=['--std=c++23'], suffix='_cpp23', name_suffix=' (C++23)', platform_system=args.platform_system, installed_clang_executable=args.installed_clang_executable)


if __name__ == '__main__':
    main()
