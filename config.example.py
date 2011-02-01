root='../../'
arch='Linux-x86-64-g95'
version='sdbg'
nproc=2
bin='${root}/exe/${arch}/cp2k.${version}'
#bin='valgrind ${root}/exe/${arch}/cp2k.${version}'
testsrc='${root}/tests'
make='make ARCH=${arch} VERSION=${version} -j${nproc}'
makedir='${root}/makefiles'
#cvs_update='cvs update -dP'
#nproc_mpi=1
#mpi_prefix='mpirun -np %i'
