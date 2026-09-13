"""Build/verify the Linux CPython 3.12 dependency bundle, never private data."""
import hashlib
import json
import os
import platform
from pathlib import Path
import subprocess
import sys
import tomllib
import zipfile
from email.parser import BytesParser


def run(*args):
    subprocess.run(args, check=True)


def main():
    if sys.platform != "linux" or platform.machine() != "x86_64" or sys.version_info[:2] != (3, 12):
        raise ValueError("qualified lock target is Linux x86_64 CPython 3.12 only")
    out = Path("dependency-bundle")
    out.mkdir(exist_ok=False)
    wheels = out / "wheels"
    wheels.mkdir()
    project = tomllib.loads(Path("pyproject.toml").read_text())
    deps = project["project"]["dependencies"]
    vcs = [d for d in deps if "git+" in d]
    if len(vcs) != 1 or not vcs[0].endswith("a90e3d884830dd267ba61faf0f5ef4c4a58c0a92"):
        raise ValueError("review changed VCS source before building")
    lock = Path("requirements-linux-py312.lock")
    if lock.exists():
        run(sys.executable, "-m", "pip", "download", "--only-binary=:all:",
            "--require-hashes", "--dest", str(wheels), "-r", str(lock))
        (out / lock.name).write_bytes(lock.read_bytes())
    else:
        requirements = [d for d in deps if "git+" not in d]
        requirements += project["project"]["optional-dependencies"]["dev"]
        requirements += project["project"]["optional-dependencies"]["live"]
        requirements += ["pip", "setuptools>=68", "wheel"]
        run(sys.executable, "-m", "pip", "install", "--dry-run", "--ignore-installed",
            "--only-binary=:all:", "--report", str(out / "resolution.json"), *requirements)
        report = json.loads((out / "resolution.json").read_text())
        lines = ["# Linux x86_64 CPython 3.12; generated from a clean resolver."]
        for item in sorted(report["install"], key=lambda i: i["metadata"]["name"].lower()):
            meta = item["metadata"]
            digest = item["download_info"]["archive_info"]["hashes"]["sha256"]
            lines.append(f'{meta["name"]}=={meta["version"]} --hash=sha256:{digest}')
        (out / lock.name).write_text("\n".join(lines) + "\n")
        run(sys.executable, "-m", "pip", "download", "--only-binary=:all:",
            "--require-hashes", "--dest", str(wheels), "-r", str(out / lock.name))
    run(sys.executable, "-m", "venv", str(out / "runtime"))
    python = str(out / "runtime/bin/python")
    run(python, "-m", "pip", "install", "--no-index", "--find-links", str(wheels),
        "--require-hashes", "-r", str(out / lock.name))
    os.environ["SOURCE_DATE_EPOCH"] = "315532800"
    os.environ["PYTHONHASHSEED"] = "0"
    run(python, "-m", "pip", "wheel", "--no-deps", "--no-build-isolation",
        "--wheel-dir", str(wheels), vcs[0])
    arp = list(wheels.glob("agent_reliability_protocol-*.whl"))
    if len(arp) != 1:
        raise ValueError("missing or ambiguous ARP wheel")
    digest = hashlib.sha256(arp[0].read_bytes()).hexdigest()
    arp_lock = f"agent-reliability-protocol==3.0.0 --hash=sha256:{digest}\n"
    frozen_arp = Path("requirements-arp.lock")
    if frozen_arp.exists() and frozen_arp.read_text() != arp_lock:
        raise ValueError("ARP wheel differs from frozen build")
    (out / "requirements-arp.lock").write_text(arp_lock)
    run(python, "-m", "pip", "install", "--no-index", "--find-links", str(wheels),
        "--require-hashes", "--no-deps", "-r", str(out / "requirements-arp.lock"))
    run(python, "-m", "pip", "install", "--no-deps", "--no-build-isolation", "-e", ".")
    run(python, "-m", "pip", "check")
    # pip check alone does not validate the root's unselected optional extras.
    run(python, "-c", "\n".join([
        "import importlib.metadata as m, tomllib",
        "from packaging.requirements import Requirement",
        "from pathlib import Path",
        "p=tomllib.loads(Path('pyproject.toml').read_text())",
        "requirements=p['project']['dependencies']+p['build-system']['requires']",
        "requirements+=p['project']['optional-dependencies']['dev']+p['project']['optional-dependencies']['live']",
        "for text in requirements:",
        " r=Requirement(text)",
        " if r.url: continue",
        " if r.marker and not r.marker.evaluate(): continue",
        " assert m.version(r.name) in r.specifier, 'lock does not satisfy '+text",
    ]))
    audit = []
    for wheel in sorted(wheels.glob("*.whl")):
        if wheel == arp[0]:
            continue
        with zipfile.ZipFile(wheel) as z:
            meta = BytesParser().parsebytes(z.read(next(n for n in z.namelist() if n.endswith(".dist-info/METADATA"))))
        audit.append(f'{meta["Name"]}=={meta["Version"]}')
    (out / "audit-requirements.txt").write_text("\n".join(audit) + "\n")
    (out / "inventory.json").write_text(json.dumps({
        "platform": sys.platform, "python": sys.version,
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "arp_source": vcs[0], "cve_scope_exclusions": {
            "agent-reliability-protocol": "VCS-only source, not a PyPI advisory identity; requires source review",
            "agent-smell-degradation-harness": "local application; dependency scanning is not SAST"},
        "wheels": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(wheels.glob("*.whl"))},
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
