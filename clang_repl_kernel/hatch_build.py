import os
import sys
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomHook(BuildHookInterface):
    def initialize(self, version, build_data):
        here = os.path.abspath(os.path.dirname(__file__))
        sys.path.insert(0, here)

        from clang_repl_kernel.install import install_my_kernel_spec

        prefix = os.path.join(here, 'data_kernelspec')
        # install_my_kernel_spec(False, prefix, suffix='')

        install_my_kernel_spec(False, prefix=prefix,
                               args=['--std=c++14'], suffix='_cpp14', name_suffix=' (C++14)')
        install_my_kernel_spec(False, prefix=prefix,
                               args=['--std=c++17'], suffix='_cpp17', name_suffix=' (C++17)')
        install_my_kernel_spec(False, prefix=prefix,
                               args=['--std=c++20'], suffix='_cpp20', name_suffix=' (C++20)')
        install_my_kernel_spec(False, prefix=prefix,
                               args=['--std=c++23'], suffix='_cpp23', name_suffix=' (C++23)')


# values = ['c++14', 'c++17', 'c++20', 'c++23']

