"""An example Jupyter kernel"""

__version__ = '1.2.18'

from .downloader import list, download, get_dll_or_download, is_done
from .kernel import ClangReplKernel, PlatformPath, ClangReplConfig, find_prog,WinShell, BashShell, Shell
from .install import install_bundles
