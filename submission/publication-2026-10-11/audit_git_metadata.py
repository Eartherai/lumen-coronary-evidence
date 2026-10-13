"""Read-only signature audit; report filenames, never matched content.

Run from any directory. Checks tracked working files, raw Git metadata and all
stored blob/commit/tag objects, including objects no longer reachable from refs.
This is a signature check, not a claim to detect every possible secret format.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[2]
PATTERNS = [
    rb"\bgh[pousr]_[A-Za-z0-9]{30,}\b",
    rb"\bgithub_pat_[A-Za-z0-9_]{40,}\b",
    rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b",
    rb"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}\b",
    rb"\bxox[baprs]-[A-Za-z0-9-]{20,}\b",
    rb"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
    rb"https?://[^\s/:]+:[^\s/@]{8,}@",
]
SIGNATURES = [re.compile(pattern) for pattern in PATTERNS]


def git(*arguments):
    return subprocess.check_output(["git", *arguments], cwd=ROOT)


def candidate(raw):
    return any(pattern.search(raw) for pattern in SIGNATURES)


def audit():
    found = set()
    tracked = [name.decode() for name in git("ls-files", "-z").split(b"\0") if name]
    working_count = 0
    for name in tracked:
        path = ROOT / name
        if path.is_file():
            working_count += 1
            if candidate(path.read_bytes()):
                found.add(name)

    git_dir = Path(git("rev-parse", "--absolute-git-dir").decode().strip())
    metadata_count = 0
    for path in sorted(git_dir.rglob("*")):
        if path.is_file():
            metadata_count += 1
            if candidate(path.read_bytes()):
                found.add(".git/" + str(path.relative_to(git_dir)))

    names = {}
    for line in git("rev-list", "--objects", "--all").decode().splitlines():
        oid, _, name = line.partition(" ")
        if name:
            names.setdefault(oid, name)
    object_count = 0
    blob_count = 0
    objects = git("cat-file", "--batch-all-objects", "--batch-check=%(objectname) %(objecttype)").decode().splitlines()
    process = subprocess.Popen(["git", "cat-file", "--batch"], cwd=ROOT,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        for row in objects:
            oid, kind = row.split()
            if kind not in {"blob", "commit", "tag"}:
                continue
            process.stdin.write((oid + "\n").encode())
            process.stdin.flush()
            header = process.stdout.readline().decode().split()
            size = int(header[2])
            raw = process.stdout.read(size)
            if len(raw) != size or process.stdout.read(1) != b"\n":
                raise RuntimeError("Incomplete Git object read")
            object_count += 1
            blob_count += kind == "blob"
            if candidate(raw):
                found.add(names.get(oid, ".git/(unreachable " + kind + " object)"))
    finally:
        process.stdin.close()
        process.wait()
    return {
        "schema_version": 1,
        "status": "candidate_matches" if found else "no_signature_matches",
        "scope": "Tracked working files, raw Git metadata and all stored blob/commit/tag objects",
        "output_policy": "Filenames only; no matched values, private content or account identity",
        "tracked_files_checked": working_count,
        "raw_git_metadata_files_checked": metadata_count,
        "git_objects_checked": object_count,
        "git_blob_objects_checked": blob_count,
        "candidate_files": sorted(found),
        "mutations": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    result = audit()
    encoded = json.dumps(result, indent=2) + "\n"
    if arguments.output:
        arguments.output.write_text(encoded)
    print(encoded, end="")
