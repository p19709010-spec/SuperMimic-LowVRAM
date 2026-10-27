"""Read-only release candidate audit for the public file lists and planned payload."""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_FILE_BYTES = 5 * 1024 * 1024

RESTRICTED_PREFIXES = (
    ".agents/",
    ".aws/",
    ".codex/",
    ".git/",
    ".local_backups/",
    ".ssh/",
    ".venv/",
    "checkpoints/",
    "data/",
    "external/",
    "logs/",
    "outputs/",
    "runs/",
)
DATA_CODE_PREFIXES = (
    "scripts/data/",
    "src/supermimic/data/",
)
RESTRICTED_PARTS = frozenset(
    {
        ".git",
        ".local_backups",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "checkpoints",
        "data",
        "external",
        "logs",
        "outputs",
        "runs",
    }
)
RESTRICTED_SUFFIXES = frozenset(
    {
        ".ckpt",
        ".csv",
        ".gif",
        ".jpeg",
        ".jpg",
        ".mjcf",
        ".mjb",
        ".mp4",
        ".npy",
        ".npz",
        ".obj",
        ".onnx",
        ".p12",
        ".pem",
        ".png",
        ".pt",
        ".pth",
        ".safetensors",
        ".stl",
        ".urdf",
        ".usd",
        ".usda",
        ".webm",
    }
)
TEXT_SUFFIXES = frozenset(
    {
        "",
        ".html",
        ".ini",
        ".json",
        ".md",
        ".py",
        ".sh",
        ".svg",
        ".toml",
        ".txt",
        ".yaml",
        ".yml",
    }
)

SECRET_PATTERNS = (
    ("aws-access-key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("github-token", re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")),
    ("openai-token", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("slack-token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("private-key", re.compile(r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY")),
    (
        "credential-assignment",
        re.compile(
            r"(?i)(?:password|passwd|api[_-]?key|secret|access[_-]?token)"
            r"\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{12,}"
        ),
    ),
)
PRIVATE_PATH_PATTERNS = (
    ("unix-home-path", re.compile(r"/(?:home|Users)/[A-Za-z0-9._-]+(?:/|\b)")),
    ("windows-home-path", re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+")),
    ("personal-email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("git-lfs-pointer", re.compile(r"version https://git-lfs\.github\.com/spec/v1")),
)


def _git(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(ROOT), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )


def _read_list(path: Path) -> list[str]:
    entries: list[str] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        entry = raw.strip()
        if not entry or entry.startswith("#"):
            continue
        candidate = Path(entry)
        if candidate.is_absolute() or ".." in candidate.parts or entry.endswith("/"):
            raise ValueError(f"{path}:{number}: invalid relative file path {entry!r}")
        if entry in entries:
            raise ValueError(f"{path}:{number}: duplicate path {entry!r}")
        entries.append(entry)
    return entries


def _nonignored_files() -> list[str]:
    completed = _git("ls-files", "--cached", "--others", "--exclude-standard")
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "git ls-files failed")
    return sorted(line for line in completed.stdout.splitlines() if line)


def _restricted_reason(relative: str) -> str | None:
    path = Path(relative)
    if any(relative == prefix.removesuffix("/") or relative.startswith(prefix) for prefix in RESTRICTED_PREFIXES):
        return "restricted path"
    is_data_code = relative.startswith(DATA_CODE_PREFIXES)
    if any(part in RESTRICTED_PARTS and not (is_data_code and part == "data") for part in path.parts):
        return "restricted path component"
    if path.suffix.lower() in RESTRICTED_SUFFIXES:
        return f"restricted file type {path.suffix.lower()}"
    return None


def _text_findings(path: Path, relative: str) -> list[dict[str, object]]:
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return []
    data = path.read_bytes()
    if b"\0" in data[:8192]:
        return []
    text = data.decode("utf-8", errors="replace")
    findings: list[dict[str, object]] = []
    for number, line in enumerate(text.splitlines(), 1):
        for rule, pattern in SECRET_PATTERNS + PRIVATE_PATH_PATTERNS:
            if pattern.search(line):
                findings.append(dict(path=relative, line=number, rule=rule))
    return findings


def audit(
    public_list: Path,
    review_list: Path,
    materialize_to: Path | None = None,
    candidate: bool = False,
) -> dict[str, object]:
    public = _read_list(public_list)
    review = _read_list(review_list)
    errors: list[str] = []
    findings: list[dict[str, object]] = []
    total_bytes = 0
    digest = hashlib.sha256()

    overlap = sorted(set(public).intersection(review))
    if overlap:
        errors.append(f"public/review overlap: {', '.join(overlap)}")

    actual = _nonignored_files()
    planned = set(public).union(review)
    for missing in sorted(set(public).difference(actual)):
        errors.append(f"planned PUBLIC file is missing or ignored: {missing}")
    if not candidate:
        for missing in sorted(set(review).difference(actual)):
            errors.append(f"planned REVIEW file is missing or ignored: {missing}")
    elif present_review := sorted(set(review).intersection(actual)):
        for relative in present_review:
            errors.append(f"REVIEW file is present in the public candidate: {relative}")
    for unclassified in sorted(set(actual).difference(planned)):
        errors.append(f"nonignored file is not classified: {unclassified}")

    if materialize_to is not None and materialize_to.exists() and any(materialize_to.iterdir()):
        raise ValueError(f"materialization directory is not empty: {materialize_to}")

    for relative in public:
        reason = _restricted_reason(relative)
        if reason:
            errors.append(f"restricted public file ({reason}): {relative}")
            continue
        path = ROOT / relative
        if not path.is_file():
            continue
        if path.is_symlink():
            errors.append(f"public symlink is not allowed: {relative}")
            continue
        size = path.stat().st_size
        total_bytes += size
        if size > MAX_FILE_BYTES:
            errors.append(f"public file exceeds 5 MiB: {relative} ({size} bytes)")
        findings.extend(_text_findings(path, relative))
        digest.update(relative.encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        if materialize_to is not None:
            destination = materialize_to / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)

    if any(("external" in Path(relative).parts) for relative in public):
        errors.append("external checkout must never be in the public candidate")

    return {
        "public_files": len(public),
        "review_files": len(review),
        "public_bytes": total_bytes,
        "public_tree_sha256": digest.hexdigest(),
        "findings": findings,
        "errors": errors,
        "materialized_to": None if materialize_to is None else str(materialize_to),
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--public-list", type=Path, default=ROOT / "release/public_files.txt"
    )
    parser.add_argument(
        "--review-list", type=Path, default=ROOT / "release/review_files.txt"
    )
    parser.add_argument(
        "--materialize",
        type=Path,
        help="copy the PUBLIC payload into a new, empty directory for a local dry run",
    )
    parser.add_argument(
        "--candidate",
        action="store_true",
        help="audit a PUBLIC-only candidate where REVIEW files must be absent",
    )
    args = parser.parse_args(argv)
    result = audit(args.public_list, args.review_list, args.materialize, args.candidate)
    print(f"PUBLIC files: {result['public_files']}")
    print(f"REVIEW files: {result['review_files']}")
    print(f"PUBLIC bytes: {result['public_bytes']}")
    print(f"PUBLIC tree SHA256: {result['public_tree_sha256']}")
    if result["materialized_to"]:
        print(f"Materialized candidate: {result['materialized_to']}")
    for finding in result["findings"]:
        print(f"FINDING {finding['rule']}: {finding['path']}:{finding['line']}")
    for error in result["errors"]:
        print(f"ERROR {error}")
    if result["findings"] or result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
