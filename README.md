# molecular-dynamics-hpc

CPU-first GROMACS workflow for reproducible molecular dynamics.

Infrastructure policy: Docker builds and scientific runs execute on a dedicated compute node. Editing, Git operations, and SSH orchestration are performed from a separate development workstation.

M0: CPU environment and CLI/storage smoke test verified on 2026-09-29. See docs/validation/m0-20260929/.
M1: system preparation, minimization, equilibration and short production.
M2: automated validation, Python analysis and dependency/image locks.
M3: measured CPU performance and HPC/Slurm portability validation.

No scientific validation, benchmark or cluster execution is claimed yet.
Use `scripts/mdc` as the normal user, without prefixing it with sudo.
The wrapper selects the local Docker socket and supplies your UID/GID.
Run `./scripts/m0` to build the CPU image and record a CLI/storage smoke test.
This test does not run an MD simulation or the GROMACS regression suite.
Generated files belong in `runs/` and are excluded from Git.
