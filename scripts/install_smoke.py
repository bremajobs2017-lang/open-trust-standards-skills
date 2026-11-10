"""Install both built artifacts in fresh venvs, without the checkout or network on sys.path."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tarfile
import tomllib
import uuid
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = {
    "accessible-html-review": ("html", {"HTML_LANG", "IMAGE_ALT", "CONTROL_NAME"}),
    "dependency-sbom-review": ("json", set()),
    "ai-risk-register": ("json", {"RISK_APPROVAL_GAP"}),
}


def safe_member(name):
    path = PurePosixPath(name)
    return (
        bool(name)
        and not path.is_absolute()
        and ".." not in path.parts
        and "\\" not in name
        and ":" not in name
    )


def inspect_artifacts(sdist, wheel):
    with tarfile.open(sdist, "r:gz") as archive:
        members = archive.getmembers()
        if (
            len({m.name for m in members}) != len(members)
            or sum(m.size for m in members) > 20_000_000
        ):
            raise ValueError(
                "Source archive has duplicate entries or exceeds the 20 MB smoke-test limit"
            )
        if any(not safe_member(m.name) or not (m.isfile() or m.isdir()) for m in members):
            raise ValueError("Source archive contains unsafe members")
        roots = {PurePosixPath(m.name).parts[0] for m in members}
        if len(roots) != 1:
            raise ValueError("Expected one source archive root")
        prefix = roots.pop()
        names = {m.name for m in members}
        if len([n for n in names if n.endswith("/SKILL.md")]) != 20:
            raise ValueError("Source distribution must contain 20 skill directories")
        for suffix in (
            "standards/registry.yaml",
            "scripts/install_smoke.py",
            "tests/fixtures/manifest.json",
        ):
            if f"{prefix}/{suffix}" not in names:
                raise ValueError("Source distribution missing QA/source data")
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        if any(not safe_member(name) for name in names):
            raise ValueError("Wheel contains unsafe paths")
        if "trust_skills/cli.py" not in names or any("/SKILL.md" in n for n in names):
            raise ValueError("Wheel contract is CLI-only; skills must ship in source distribution")
    return prefix


def execute(command, cwd, env, expected=0):
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=180,
        check=False,
    )
    if completed.returncode != expected:
        raise RuntimeError(
            f"Smoke step failed: {command[0]} (exit {completed.returncode}); {completed.stderr[-2000:]}"
        )
    return completed.stdout


def clean_environment(environ, wheelhouse):
    env = {
        k: v
        for k, v in environ.items()
        if not k.upper().startswith(("PIP_", "PYTHON")) and k.upper() != "VIRTUAL_ENV"
    }
    env.update(
        PYTHONNOUSERSITE="1",
        PYTHONIOENCODING="utf-8",
        PIP_CONFIG_FILE=os.devnull,
        PIP_NO_INDEX="1",
        PIP_FIND_LINKS=str(wheelhouse),
        PIP_DISABLE_PIP_VERSION_CHECK="1",
        PIP_NO_CACHE_DIR="1",
    )
    return env


def smoke(sdist, wheel, wheelhouse, work_root):
    prefix = inspect_artifacts(sdist, wheel)
    work_root.mkdir(parents=True, exist_ok=True)
    work = work_root / f"install-smoke-{uuid.uuid4().hex}"
    work.mkdir()  # Retained for inspection; never deletes user-selected directories.
    source_root = work / "source"
    with tarfile.open(sdist, "r:gz") as archive:
        archive.extractall(source_root, filter="data")
    source = source_root / prefix
    env = clean_environment(os.environ, wheelhouse)
    evidence = []
    for kind, artifact in (("sdist", sdist), ("wheel", wheel)):
        base = work / kind
        base.mkdir()
        environment = base / "venv"
        execute([sys.executable, "-m", "venv", str(environment)], base, env)
        executable = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        cli = environment / ("Scripts/trust-skills.exe" if os.name == "nt" else "bin/trust-skills")
        execute(
            [
                str(executable),
                "-m",
                "pip",
                "install",
                "--no-index",
                "--find-links",
                str(wheelhouse),
                str(artifact),
            ],
            base,
            env,
        )
        location = execute(
            [str(executable), "-I", "-c", "import trust_skills; print(trust_skills.__file__)"],
            base,
            env,
        ).strip()
        if not Path(location).resolve().is_relative_to(environment.resolve()):
            raise RuntimeError("Import resolved outside the clean environment")
        execute([str(executable), "-m", "pip", "check"], base, env)
        execute([str(cli), "--help"], base, env)
        names = execute([str(cli), "list"], base, env).splitlines()
        if len(names) != 20 or len(set(names)) != 20:
            raise RuntimeError("Expected 20 CLI helpers")
        for name, (ext, codes) in EXAMPLES.items():
            result = json.loads(
                execute(
                    [
                        str(cli),
                        "run",
                        name,
                        "--input",
                        str(source / f"skills/{name}/examples/input.{ext}"),
                    ],
                    base,
                    env,
                )
            )
            if {f["code"] for f in result["findings"]} != codes:
                raise RuntimeError("Unexpected example findings")
            execute(
                [
                    str(cli),
                    "run",
                    name,
                    "--input",
                    str(source / f"skills/{name}/examples/input.{ext}"),
                    "--format",
                    "markdown",
                ],
                base,
                env,
            )
        # Bare installations must fail source validation clearly; an explicit source tree works.
        execute([str(cli), "validate", "--root", str(base)], base, env, expected=2)
        validation = json.loads(execute([str(cli), "validate", "--root", str(source)], base, env))
        if validation["skills_validated"] != 20:
            raise RuntimeError("Source validation failed")
        evidence.append(
            {
                "artifact": artifact.name,
                "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                "kind": kind,
                "status": "passed",
                "cli_helpers": len(names),
                "examples": list(EXAMPLES),
                "agent_host_tested": False,
            }
        )
    result = {
        "python": sys.version.split()[0],
        "installations": evidence,
        "source_data_contract": "sdist includes skills; wheel contains CLI only; no host installation performed",
    }
    (work / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist-dir", type=Path, default=ROOT / "dist")
    parser.add_argument(
        "--wheelhouse",
        required=True,
        type=Path,
        help="Pre-downloaded runtime/build wheels; no network fallback",
    )
    parser.add_argument("--work-dir", type=Path, default=ROOT / "tmp")
    args = parser.parse_args(argv)
    version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "version"
    ]
    stem = f"open_trust_standards_skills-{version}"
    try:
        result = smoke(
            (args.dist_dir / f"{stem}.tar.gz").resolve(),
            (args.dist_dir / f"{stem}-py3-none-any.whl").resolve(),
            args.wheelhouse.resolve(),
            args.work_dir.resolve(),
        )
    except (
        OSError,
        ValueError,
        RuntimeError,
        subprocess.TimeoutExpired,
        tarfile.TarError,
        zipfile.BadZipFile,
    ) as exc:
        print(f"Installation smoke FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
