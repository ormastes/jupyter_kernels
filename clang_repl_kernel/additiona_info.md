# Additional info

## Build LLVM

```bash
cd llvm-project
mkdir build
cd build
# windows
cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo -DLLVM_ENABLE_PROJECTS=clang -DLLVM_ENABLE_RUNTIMES="libcxx;libcxxabi;libunwind"  ../llvm
cmake --build . --target clang clang-repl runtimes           
# linux
cmake  -G "Unix Makefiles" -DCMAKE_BUILD_TYPE=RelWithDebInfo -DLLVM_ENABLE_PROJECTS=clang -DLLVM_ENABLE_RUNTIMES="libcxx;libcxxabi;libunwind"  ../llvm
cmake --build . --target clang clang-repl runtimes                                                             
```