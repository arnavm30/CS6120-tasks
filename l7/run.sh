cd llvm-pass-skeleton
mkdir build
cd build
cmake ..
make
cd ..
`brew --prefix llvm`/bin/clang -fpass-plugin=`echo build/skeleton/SkeletonPass.*` -emit-llvm -S -o - something.c