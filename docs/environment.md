# Initial execution profile

Observed on ComputeNode, 2026-09-27:
- Intel Core i3-6100T: 2 physical cores, 4 logical CPUs.
- 7.6 GiB total RAM; 6.9 GiB available at the diagnostic snapshot.
- 81 GiB reported available on the root filesystem.
- Docker requires sudo for the current user.

Verified runtime limits (reviewed 2026-09-29): 2 logical-CPU equivalents, 2 GiB RAM, no swap.
These are runtime limits, not Docker image build limits.
Compilation is explicitly serial to reduce contention on the shared host.
GROMACS uses AVX2_256, thread-MPI and OpenMP; GPU and external MPI are disabled.
An eventual run must explicitly select its thread counts (for example,
`-ntmpi 1 -ntomp 2`); OMP_NUM_THREADS alone does not constrain every program.

Ubuntu package versions and the base tag are not fully locked at M0.
The source version/checksum and in-image provenance are an initial record,
not a claim of bitwise-reproducible image rebuilds or scientific validity.
No files are placed under /srv/syncthing. Existing services are not managed.
