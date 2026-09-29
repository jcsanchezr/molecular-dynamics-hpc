# M1a: SPC/E water preparation and coarse energy minimization

Status at authoring (2026-09-29): workflow prepared; real GROMACS execution
and scientific results are NOT yet verified. M0 is recorded at commit 836e9fa.

## Scope and numerical choices

A 3 nm cubic, periodic box of pure water is generated with `gmx solvate`
from the `spc216.gro` coordinates included in GROMACS 2026.2. The actual
molecule count is measured, not assumed. SPC/E parameters and rigid-water
SETTLE constraints come from `amber99sb-ildn.ff/spce.itp`; there is no
protein or ion in this case. The seed's name does not select the model:
the topology does. Its hash and force-field file hashes are saved per run.

Steepest descent, at most 2000 steps, emstep 0.01 nm, emtol 1000
kJ mol^-1 nm^-1. PME electrostatics, 1 nm Coulomb/LJ cutoffs, fourth-order
PME interpolation with 0.12 nm grid spacing, dispersion correction.
This is a deliberately coarse initial relaxation threshold, NOT a precise
energy minimum, an equilibrium test, or a parameter recommendation for
arbitrary molecular systems. Follow-up MD requires separate validation.

## Execution

Run `./scripts/m1a` as compute-user on ComputeNode. All computation uses the existing
M0 CPU image, 1 thread-MPI rank and 2 OpenMP threads. The execution-only
Compose overlay removes the build definition and disables image pulls.
The M0 image ID is checked before starting. The runtime keeps the M0 limits
and read-only mounts; tests/ is additionally mounted read-only. Inputs,
workflow, checker and tests are snapshotted under runs/M1A_ID/source/.

No OS package installation, image build, GPU, external download, database,
Git commit, push or modification of other containers is performed.
The runner refuses another invocation while its lock is held or another
container of this Compose project is running. A new run always has a new
output directory. Do not restart blindly after disconnecting SSH.

## Acceptance and evidence

`grompp` runs with its default zero-warning allowance. Never increase
`-maxwarn` merely to get past an error. All execution exit statuses are
checked. `check_water_em.py` additionally requires finite coordinates and
energies, consistent water atom/molecule counts, unchanged 3 nm box,
Fmax < emtol, and no endpoint potential-energy increase (allowing output
rounding). Final energy in the log must agree with the extracted value.
A summary.json status of PASS meets only this coarse preparation gate.
Synthetic unittest fixtures exercise the checker, not the physics.

Runs include the seed, prepared and minimized structures, source snapshots,
processed MDP/topology, TPR, energy data, command logs, hashes, and summary.
`gmx energy` averages from minimization are NOT equilibrium statistics.
M1b will cover equilibration and short dynamics; M1 is not closed by M1a.
No benchmark, protein result, regression-suite validation or HPC run is claimed.

## Primary references (accessed 2026-09-29)

- https://manual.gromacs.org/documentation/2026.2/onlinehelp/gmx-solvate.html
- https://manual.gromacs.org/documentation/2026.2/user-guide/mdp-options.html
- https://manual.gromacs.org/documentation/2026.2/onlinehelp/gmx-grompp.html
- https://manual.gromacs.org/documentation/2026.2/onlinehelp/gmx-mdrun.html
- https://manual.gromacs.org/documentation/2026.2/onlinehelp/gmx-energy.html
- https://raw.githubusercontent.com/gromacs/gromacs/v2026.2/share/top/amber99sb-ildn.ff/spce.itp
- https://docs.docker.com/reference/compose-file/merge/
- https://docs.docker.com/reference/cli/docker/compose/run/

## Review addendum - 2026-09-29

The first real run, m1a-20260929T194014Z-1222011, reached the numerical
minimization threshold but emitted a SETTLE diagnostic at step 11.
Its original checker returned PASS because it did not inspect that class
of diagnostic. The original run and summary remain preserved.

The revised checker adds a conservative diagnostic review gate. A matched
SETTLE/LINCS/constraint/fatal diagnostic, or missing required diagnostic log,
returns REVIEW_REQUIRED even when the numerical checks pass. This is a
project audit policy, not a claim that any rejected minimization trial
invalidates the final coordinates. See docs/validation/m1a-20260929-review/.
No simulation parameters were changed by this checker correction. M1a is
not yet closed and M1b has not started.

## First real execution — 2026-09-29

Run:
`runs/m1a-20260929T194014Z-1222011`

Observed system:

- 884 SPC/E water molecules
- 2652 atoms
- 3 x 3 x 3 nm periodic box
- steepest descent converged in 13 reported steps
- final Fmax: 947.97675 kJ mol^-1 nm^-1
- emtol: 1000 kJ mol^-1 nm^-1
- initial potential energy: -4144.825195 kJ/mol
- final potential energy: -40957.9375 kJ/mol

The original validator returned PASS for its numerical checks. A subsequent
read-only review found a SETTLE diagnostic at step 11 in both em.log and
mdrun-console.log. The validation policy was therefore strengthened and the
run is classified REVIEW_REQUIRED rather than a clean M1a completion.

The original run directory was verified byte-for-byte unchanged by the review
procedure. No time-dependent molecular dynamics has been claimed.

Next controlled experiment: repeat the same preparation/minimization with only
the steepest-descent initial maximum displacement reduced from emstep=0.01 nm
to emstep=0.001 nm. M1b must not start until this diagnostic is resolved.
