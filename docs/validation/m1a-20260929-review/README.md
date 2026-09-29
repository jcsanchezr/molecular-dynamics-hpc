# M1a retrospective review - 2026-09-29

Run: runs/m1a-20260929T194014Z-1222011
Base commit: 836e9fa. M1a source was uncommitted but snapshotted in the run.
The original checker reported PASS based on its numerical checks. It did
not inspect constraint diagnostics. The original summary and all run files
remain unchanged; original-summary.json preserves the old assessment.

GROMACS reached Fmax < 1000 in 13 reported iterations (884 waters,
2652 atoms, 3 nm cube). It also reported a SETTLE constraint diagnostic at
step 11. For steepest descent, GROMACS 2026.2 can reject a trial with failed
constraints and continue. This diagnostic alone is NOT proof that final
coordinates are invalid. It must nevertheless be visible to reviewers.

The revised gate requires non-empty em.log and mdrun-console.log, flags
selected SETTLE/LINCS/constraint/fatal diagnostics, and retains the numerical
checks. Flags produce REVIEW_REQUIRED, not automatic acceptance or a claim
of invalid physics. The scanner is not an exhaustive scientific validator.
The number of recorded matches is NOT a number of unique events: the same
message can appear in both log files.

Candidate synthetic tests ran using the existing M0 image. The revised
checker reviewed existing files using --stdout-only. No minimization, MD,
image build, image pull, scientific-parameter change or Git commit occurred.
Before/after manifests confirmed all historical run-file contents unchanged.

M0 remains complete. M1a converged numerically but remains under review.
Next: inspect final geometry and/or a documented controlled comparison of
initial emstep, without hiding or overwriting the original diagnostic.
This is NOT a 12 ps MD trajectory or a validation of equilibrium properties.

Primary source: GROMACS v2026.2 src/gromacs/mdrun/minimize.cpp,
https://raw.githubusercontent.com/gromacs/gromacs/v2026.2/src/gromacs/mdrun/minimize.cpp
