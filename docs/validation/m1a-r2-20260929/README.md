# M1a-r2 validation — SPC/E water minimization

Date: 2026-09-29

Run:
`runs/m1a-20260929T200757Z-1227519`

Controlled change relative to r1:

- `emstep`: 0.01 nm -> 0.001 nm

Held constant:

- GROMACS 2026.2 CPU image
- SPC/E water
- 3 x 3 x 3 nm periodic box
- 884 water molecules / 2652 atoms
- `emtol = 1000 kJ mol^-1 nm^-1`
- thread-MPI/OpenMP execution profile and resource limits

Observed result:

- steepest descent converged in 17 steps
- final Fmax: 672.02136 kJ mol^-1 nm^-1
- initial potential: -4144.825195 kJ/mol
- final potential: -37424.300781 kJ/mol
- no SETTLE/LINCS/fatal diagnostics detected by validation policy
- validation status: PASS

This closes the M1a coarse preparation/minimization gate.
It is not an equilibrium test, production MD, benchmark or HPC validation.
