"""An example Jupyter kernel"""

__version__ = '1.1.18'

from .downloader import list, download
from .kernel import ClangReplKernel, PlatformPath, ClangReplConfig, find_prog,WinShell, BashShell, Shell
from .install import install_bundles
