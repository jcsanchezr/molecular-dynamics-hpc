"""Validate a first water minimization with Python's standard library only.

These checks establish a coarse preparation gate, not physical validation
of equilibrium properties or an exact minimum. Selected runtime diagnostics
also require review. Use --stdout-only when reviewing historical evidence.
Run inside the CPU image.
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path


def finite(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise ValueError(f"Non-finite value: {token}")
    return value


def gro_count(path: Path) -> int:
    lines = path.read_text().splitlines()
    count = int(lines[1])
    if count <= 0 or count % 3 or len(lines) != count + 3:
        raise ValueError(f"Invalid three-site water atom count in {path.name}")
    for i, line in enumerate(lines[2:2 + count]):
        expected = ("OW", "HW1", "HW2")[i % 3]
        if line[5:10].strip() != "SOL" or line[10:15].strip() != expected:
            raise ValueError(f"Unexpected water atom in {path.name}: {i + 1}")
        for start in (20, 28, 36):
            finite(line[start:start + 8])
    box = [finite(x) for x in lines[-1].split()]
    if len(box) != 3 or any(abs(x - 3.0) > 1e-4 for x in box):
        raise ValueError(f"Expected a 3 nm cubic box in {path.name}")
    return count


def last_log_number(text: str, label: str) -> float:
    matches = re.findall(r"^\s*" + re.escape(label) + r"\s*=\s*(\S+)",
                         text, flags=re.MULTILINE)
    if not matches:
        raise ValueError(f"Missing final {label} in em.log")
    return finite(matches[-1])



def execution_diagnostics(run: Path) -> list[dict[str, object]]:
    """Report selected constraint/runtime diagnostics; not an exhaustive scanner.

    A rejected steepest-descent trial may recover. REVIEW_REQUIRED is an
    audit gate, not a claim that the final coordinates are necessarily invalid.
    Missing console evidence fails closed. Duplicate log lines are kept with
    their source locations; the list length is NOT a count of unique events.
    """
    patterns = (
        ("SETTLE_DIAGNOSTIC", r"water molecules\s+can\s*(?:not|'t)\s+be settled"),
        ("LINCS_WARNING", r"\bLINCS\s+WARNING\b"),
        ("CONSTRAINT_FAILURE", r"constraint(?:s)?\s+(?:failure|failed|error)"),
        ("UNCONSTRAINED_COORDINATES", r"coordinates could not be constrained"),
        ("FATAL_ERROR", r"\bFatal error\s*:"),
    )
    findings = []
    for name in ("em.log", "mdrun-console.log"):
        path = run / name
        if not path.is_file() or path.stat().st_size == 0:
            findings.append({"code": "MISSING_DIAGNOSTIC_LOG", "file": name})
            continue
        for number, line in enumerate(path.read_text().splitlines(), 1):
            for code, pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append({"code": code, "file": name,
                                     "line": number, "text": line.strip()})
                    break
    return findings

def assess(run: Path) -> dict[str, object]:
    initial_count = gro_count(run / "water.gro")
    final_count = gro_count(run / "em.gro")
    if initial_count != final_count:
        raise ValueError("Atom count changed during minimization")
    # The original topology contains no SOL entry; solvate adds exactly one.
    counts = re.findall(r"^\s*SOL\s+(\d+)\s*(?:;.*)?$",
                        (run / "topol.top").read_text(), re.MULTILINE)
    if len(counts) != 1 or int(counts[0]) * 3 != initial_count:
        raise ValueError("Topology SOL count does not match coordinates")
    mdp = (run / "em.mdp").read_text()
    tolerance_match = re.search(r"^\s*emtol\s*=\s*(\S+)", mdp, re.MULTILINE)
    if tolerance_match is None:
        raise ValueError("Missing emtol")
    tolerance = finite(tolerance_match[1])
    if tolerance <= 0:
        raise ValueError("emtol must be positive")
    log = (run / "em.log").read_text()
    fmax = last_log_number(log, "Maximum force")
    final_log_energy = last_log_number(log, "Potential Energy")
    energies = []
    for line in (run / "potential.xvg").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "@")):
            continue
        columns = line.split()
        if len(columns) != 2:
            raise ValueError("Expected one energy column in potential.xvg")
        finite(columns[0])
        energies.append(finite(columns[1]))
    if not energies:
        raise ValueError("No potential-energy samples")
    slack = max(0.01, abs(energies[0]) * 1e-6)
    diagnostics = execution_diagnostics(run)
    checks = {
        "maximum_force_below_emtol": 0 <= fmax < tolerance,
        "potential_did_not_increase": energies[-1] <= energies[0] + slack,
        "final_energy_matches_log": abs(final_log_energy - energies[-1])
        <= max(0.1, abs(final_log_energy) * 1e-5),
    }
    numerical_pass = all(checks.values())
    checks["constraint_diagnostics_absent"] = not diagnostics
    return {
        "validation_policy": "water-em-v2-diagnostic-gate",
        "numerical_checks_passed": numerical_pass,
        "diagnostics": diagnostics,
        "status": "PASS" if all(checks.values()) else "REVIEW_REQUIRED",
        "stage": "M1a preparation and coarse energy minimization; NOT MD",
        "atoms": initial_count,
        "water_molecules": initial_count // 3,
        "box_nm": [3.0, 3.0, 3.0],
        "maximum_force_kj_mol_nm": fmax,
        "emtol_kj_mol_nm": tolerance,
        "potential_initial_kj_mol": energies[0],
        "potential_final_kj_mol": energies[-1],
        "energy_samples": len(energies),
        "checks": checks,
    }


def main() -> int:
    args = sys.argv[1:]
    stdout_only = bool(args and args[0] == "--stdout-only")
    if stdout_only:
        args = args[1:]
    if len(args) != 1:
        print("Usage: check_water_em.py [--stdout-only] RUN_DIRECTORY", file=sys.stderr)
        return 2
    run = Path(args[0])
    try:
        report = assess(run)
    except (OSError, ValueError, IndexError) as exc:
        report = {"status": "REVIEW_REQUIRED", "reason": str(exc)}
    text = json.dumps(report, indent=2, allow_nan=False) + "\n"
    if not stdout_only:
        (run / "summary.json").write_text(text)
    print(text, end="")
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
