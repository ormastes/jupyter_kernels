"""An example Jupyter kernel"""

__version__ = '1.6.22'

from .downloader import list, download, get_dll_or_download, is_done
from .kernel import ClangReplKernel, PlatformPath, ClangReplConfig, find_prog,WinShell, BashShell, Shell, update_platform_system, CLANG_REPL_DEBUG
from .install import install_bundles, is_installed_clang_exist
