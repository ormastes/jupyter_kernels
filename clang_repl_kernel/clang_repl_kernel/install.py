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
from clang_repl_kernel import ClangReplConfig

kernel_json = {
    "argv": [ClangReplConfig.PYTHON_EXE, "-m", "clang_repl_kernel", "-f", "{connection_file}"],
    "display_name": "Clang-Repl",
    "language": "c++",
    "env": {"CPLUS_INCLUDE_PATH":""}
}


def install_my_kernel_spec(user=True, prefix=None, args=None, suffix=None, name_suffix='', platform_system=platform.system()):
    with TemporaryDirectory() as td:
        os.chmod(td, 0o755)  # Starts off as 700, not user readable
        local_kernel_json = kernel_json.copy()
        local_kernel_json['argv'].extend(args)
        local_kernel_json['display_name'] += name_suffix
        my_env = os.environ.copy()
        #local_kernel_json['env']['CPLUS_INCLUDE_PATH'] = my_env.get('CPLUS_INCLUDE_PATH', '')
        for key in my_env:
            local_kernel_json['env'][key] = my_env[key]
            print(key + " = " + my_env[key])
        if len(my_env) == 0:
            print("No environment variables found. Please set CPLUS_INCLUDE_PATH manually")
            local_kernel_json['env']['EMPTY'] = 'True'
        #if False:# local_kernel_json['env']['CPLUS_INCLUDE_PATH'] == '':
            # get input from user
            #local_kernel_json['env']['CPLUS_INCLUDE_PATH'] = \
            #    input("Please enter the path to the C++ include directory (where 'stddef.h is located)\n For example: /usr/lib/llvm-18/lib/clang/18/include : ")

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
        install_bundles(platform_system)

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

def install_bundles(platform_system):
    if platform_system == 'Windows':
        platform_system = 'WinMG64'
    elif platform_system == 'Linux':
        platform_system = 'Lin64'

    # currently does not work. See https://gist.github.com/fkraeutli/66fa741d9a8c2a6a238a01d17ed0edc5 for details
    files = {
        'WinMG32': 'https://mega.nz/file/iU0W2CBK#gIw33d3aP0G_CYJz8cokXHqlCDmOS9VGX91HTmjOB7M',
        'WinMG64': 'https://mega.nz/file/jdEg2bBK#faSU0VkFd8izmq7Ydzf6dAHxau1qxZ2aPZKt-Ow7PIo',
        'Lin64': 'https://mega.nz/folder/iFdXmb6L#RKO8HmgjgVj3Mv3M1LYE7g/file/fN9EkbrK',
        'Lin32': 'https://mega.nz/folder/iFdXmb6L#RKO8HmgjgVj3Mv3M1LYE7g/file/fN9EkbrK',
    }

    ClangReplConfig.set_platform(ClangReplConfig.get_default_platform())
    if not os.path.exists(ClangReplConfig.get_bin_path()):
        url = files[platform_system]
        zip_filename = platform_system+".zip"
        extract_dir = ClangReplConfig.get_install_dir()
        print("Downloading clang_repl binary from " + url)
        try:
            #subprocess.run(["mega-get.bat", files[platform_system], platform_system+".zip"]) add current env path
            env = os.environ.copy()
            response = subprocess.run(["mega-get"+ClangReplConfig.SCRIPT_EXT, url, zip_filename], env=env)
        except Exception as e:
            print("Mega CLI not found. Please install it from https://mega.io/cmd#downloadapps")
            print("May need path to C:/Users/[USERNAME]/AppData/Local/MEGAcmd")
            return

        if response.returncode == 0 : # response.status_code == 200:
            print("Download successful")

            # Unzip the contents into the extract_dir
            with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            print("Unzip complete. Files extracted to:", extract_dir)
            # Remove the zip file
            os.remove(zip_filename)
        else:
            print("Download failed with status code " + str(response.returncode)) #str(response.status_code))
            print("Please download the binary manually and place it in default path.")
            print("The clang-repl binary can be build from source. See https://clang.llvm.org/docs/ClangRepl.html")


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
                    help="Platform system (Linux, Windows, Win_i386_MT, Win_i386_MD, Win_x64_MT, Win_x64_MD)", 
                    default=platform.system())
    args = ap.parse_args(argv)

    if args.sys_prefix:
        args.prefix = sys.prefix
    if not args.prefix and not _is_root():
        args.user = True

    install_my_kernel_spec(user=args.user, prefix=args.prefix,
                           args=['--std=c++14'], suffix='_cpp14', name_suffix=' (C++14)', platform_system=args.platform_system)
    install_my_kernel_spec(user=args.user, prefix=args.prefix,
                           args=['--std=c++17'], suffix='_cpp17', name_suffix=' (C++17)', platform_system=args.platform_system)
    install_my_kernel_spec(user=args.user, prefix=args.prefix,
                           args=['--std=c++20'], suffix='_cpp20', name_suffix=' (C++20)', platform_system=args.platform_system)
    install_my_kernel_spec(user=args.user, prefix=args.prefix,
                           args=['--std=c++23'], suffix='_cpp23', name_suffix=' (C++23)', platform_system=args.platform_system)


if __name__ == '__main__':
    main()
