# M0 environment verification

Build completed: 2026-09-27. Evidence reviewed: 2026-09-29.
Host: ComputeNode. All Docker builds and runs remain on this host.
Build duration reported by BuildKit: 33m 18s.
Build record: 56xpokq06sudvt24q0dvqwf44.
Original logs: runs/m0-20260927T204014Z-773166/.
Local image: molecular-dynamics-hpc:gmx2026.2-cpu.
Local image ID reported by Docker inspect:
sha256:e6d20f0d1198056f9b842510d7e7e75bb4677a8597d268db78cc8fac49739e73

Verified: GROMACS 2026.2 CLI, CPU-only, thread-MPI, OpenMP,
AVX2_256, non-root execution, installed water-coordinate data,
and persistent output owned by the invoking host user.
Observed limits: 2 CPU equivalents, 2147483648 bytes RAM, no swap.
Python in the image: 3.12.3; scientific analysis is not implemented yet.

This is a CLI/data/storage smoke test, not an MD simulation,
a GROMACS regression-suite run, a benchmark or HPC validation.
Base-image and package locks remain pending; the recorded local image
ID is not proof of a published image or bitwise-reproducible rebuilds.

Selected raw evidence is copied here; SHA256SUMS covers these copies.
Full build.log and CMakeCache.txt remain in the original run directory.
