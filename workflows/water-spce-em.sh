#!/usr/bin/env bash
# Container entry point. All writes stay in this run's persistent directory.
set -Eeuo pipefail
export LC_ALL=C PYTHONDONTWRITEBYTECODE=1
[[ $# == 1 && "$1" =~ ^m1a-[0-9]{8}T[0-9]{6}Z-[0-9]+$ ]] || exit 2
cd "/workspace/runs/$1"
trap 'rc=$?; printf "WORKFLOW FAILED (rc=%s, line=%s). Keep this run.\n" "$rc" "$LINENO" >&2; exit "$rc"' ERR
[[ "$(id -u)" != 0 ]]
lib=/opt/gromacs/share/gromacs/top
ff="$lib/amber99sb-ildn.ff"
for f in "$lib/spc216.gro" "$ff/forcefield.itp" "$ff/spce.itp"; do
    test -s "$f"
done
printf '\n===== 1. RUNTIME AND VALIDATOR TESTS =====\n'
gmx --version > gromacs-version.txt 2>&1
grep -Eq '^GROMACS version:[[:space:]]+2026\.2[[:space:]]*$' gromacs-version.txt
grep -Eq '^GPU support:[[:space:]]+disabled[[:space:]]*$' gromacs-version.txt
{
    id
    printf 'cpu.max: '; cat /sys/fs/cgroup/cpu.max
    printf 'memory.max: '; cat /sys/fs/cgroup/memory.max
    printf 'memory.swap.max: '; cat /sys/fs/cgroup/memory.swap.max
} | tee runtime.txt
grep -Fxq 'cpu.max: 200000 100000' runtime.txt
grep -Fxq 'memory.max: 2147483648' runtime.txt
grep -Fxq 'memory.swap.max: 0' runtime.txt
# Source snapshots were copied by the host runner before starting Docker.
python3 source/tests/test_water_em.py -v 2>&1 | tee validator-tests.txt
cp source/inputs/water-spce/topol.template.top topol.top
cp source/inputs/water-spce/em.mdp em.mdp
cp "$lib/spc216.gro" seed-spc216.gro
sha256sum seed-spc216.gro > seed.sha256
find "$ff" -type f -print0 | sort -z | xargs -0 sha256sum > forcefield.sha256
printf '\n===== 2. PREPARE THE WATER BOX =====\n'
gmx solvate -cs seed-spc216.gro -box 3 3 3 -o water.gro -p topol.top \
    2>&1 | tee solvate.log
printf '\n===== 3. PREPROCESS WITHOUT OVERRIDING WARNINGS =====\n'
gmx grompp -f em.mdp -c water.gro -p topol.top -o em.tpr \
    -po em.processed.mdp -pp em.processed.top 2>&1 | tee grompp.log
printf '\n===== 4. ENERGY MINIMIZATION (NOT TIME-DEPENDENT MD) =====\n'
gmx mdrun -s em.tpr -deffnm em -ntmpi 1 -ntomp 2 -pin off \
    -nb cpu -pme cpu 2>&1 | tee mdrun-console.log
printf '\n===== 5. EXTRACT AND CHECK RESULTS =====\n'
printf 'Potential\n0\n' | gmx energy -f em.edr -o potential.xvg -xvg none \
    2>&1 | tee energy-extraction.log
for f in em.gro em.edr em.log em.tpr; do test -s "$f"; done
python3 source/analysis/check_water_em.py "$PWD" | tee summary.txt
sha256sum water.gro topol.top em.mdp em.processed.mdp em.processed.top \
    em.tpr em.gro em.edr em.log potential.xvg summary.json > output.sha256
printf '\nM1A PASS: water prepared and coarse minimization checked. NOT an MD trajectory.\n'
