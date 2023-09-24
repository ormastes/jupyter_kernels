import argparse
import json
import os
import sys
import shutil
import requests

from jupyter_client.kernelspec import KernelSpecManager
from tempfile import TemporaryDirectory

from clang_repl_kernel import DefaultText

kernel_json = {
    "argv": [sys.executable, "-m", "clang_repl_kernel", "-f", "{connection_file}"],
    "display_name": "Clang-Repl",
    "language": "c++",
}


def install_my_kernel_spec(user=True, prefix=None, args=None, suffix=None, name_suffix=''):
    with TemporaryDirectory() as td:
        os.chmod(td, 0o755)  # Starts off as 700, not user readable
        local_kernel_json = kernel_json.copy()
        local_kernel_json['argv'].extend(args)
        local_kernel_json['display_name'] += name_suffix
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

        if os.path.exists(DefaultText.BIN_PATH):
            # make directory DefaultText.BIN_REL_DIR if it doesn't exist
            os.makedirs(os.path.join(td, DefaultText.BIN_REL_DIR), exist_ok=True)
            shutil.copy(DefaultText.BIN_PATH, os.path.join(td, DefaultText.BIN_REL_PATH))
        else:
            url = "https://github.com/ormastes/jupyter_kernels/clang_repl_kernel/" + DefaultText.BIN_REL_DIR + "/" \
                  + DefaultText.BIN + "?raw=true"
            print("Downloading clang_repl binary from " + url)
            req = requests.get(url, stream=True)
            if req.status_code == 200:
                print("Download successful")
                os.makedirs(os.path.join(td, DefaultText.BIN_REL_DIR), exist_ok=True)
                with open(os.path.join(td, DefaultText.BIN_REL_PATH), "wb") as _fh:
                    req.raw.decode_content = True
                    shutil.copyfileobj(req.raw, _fh)
            else:
                print("Download failed with status code " + str(req.status_code))
                print("Please download the binary manually and place it in default path.")
                print("The clang-repl binary can be build from source. See https://clang.llvm.org/docs/ClangRepl.html")

        KernelSpecManager().install_kernel_spec(td, 'clang_repl' + suffix, user=user, prefix=prefix)


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
    args = ap.parse_args(argv)

    if args.sys_prefix:
        args.prefix = sys.prefix
    if not args.prefix and not _is_root():
        args.user = True

    #install_my_kernel_spec(user=args.user, prefix=args.prefix,
    #                       args=['-std=c++14'], suffix='_cpp14', name_suffix=' (C++14)')
    #install_my_kernel_spec(user=args.user, prefix=args.prefix,
    #                       args=['-std=c++17'], suffix='_cpp17', name_suffix=' (C++17)')
    #install_my_kernel_spec(user=args.user, prefix=args.prefix,
    #                       args=['-std=c++20'], suffix='_cpp20', name_suffix=' (C++20)')
    install_my_kernel_spec(user=args.user, prefix=args.prefix,
                           args=['-std=c++23'], suffix='_cpp23', name_suffix=' (C++23)')


if __name__ == '__main__':
    main()
