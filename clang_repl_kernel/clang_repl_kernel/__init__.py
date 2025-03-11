"""An example Jupyter kernel"""

__version__ = '1.5.18'

from .downloader import list, download, get_dll_or_download, is_done
from .kernel import ClangReplKernel, PlatformPath, ClangReplConfig, find_prog,WinShell, BashShell, Shell
from .install import install_bundles, is_installed_clang_exist
