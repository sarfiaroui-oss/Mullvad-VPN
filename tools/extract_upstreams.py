#!/usr/bin/env python3
"""Recreate the local upstream inspection workspace without changing source files."""

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "build" / "upstream"
ARCHIVES = (
    ("mullvadvpn-app-main.zip", "mullvadvpn-app-main", "mullvad",
     "95d77642fd18ded01423c9bf125f22159479dfd058dbb801cf286f425d98ba6f"),
    ("amnezia-client-dev.zip", "amnezia-client-dev", "amnezia",
     "f32e784d47c196158728eee8df7aeef01093df6368ebc72a142d0829a9cebcd0"),
)


def entries(archive, prefix):
    result = []
    seen = set()
    links = set()
    for info in archive.infolist():
        path = PurePosixPath(info.filename)
        if (path.is_absolute() or ".." in path.parts or "\\" in info.filename
                or not path.parts or path.parts[0] != prefix):
            raise ValueError(f"Unexpected archive path: {info.filename}")
        relative = Path(*path.parts[1:])
        if relative == Path("."):
            if not info.is_dir():
                raise ValueError("Archive root must be a directory")
            continue
        if relative in seen:
            raise ValueError(f"Duplicate archive path: {relative}")
        seen.add(relative)
        mode = info.external_attr >> 16
        if stat.S_ISLNK(mode):
            links.add(relative)
        elif stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR):
            raise ValueError(f"Unsupported archive file type: {relative}")
        result.append((info, relative, mode))
    for _, relative, _ in result:
        if any(parent in links for parent in relative.parents):
            raise ValueError(f"Archive writes through a symlink: {relative}")
    return result


def verify(archive, members, destination):
    for info, relative, mode in members:
        path = destination / relative
        for parent in (destination, *path.parents):
            if parent == ROOT:
                break
            if parent.is_symlink():
                raise ValueError(f"Refusing a symlink directory: {parent}")
        if stat.S_ISLNK(mode):
            matches = path.is_symlink() and os.readlink(path) == archive.read(info).decode()
        elif info.is_dir():
            matches = path.is_dir() and not path.is_symlink()
        else:
            matches = (path.is_file() and not path.is_symlink()
                       and path.read_bytes() == archive.read(info))
        if not matches:
            raise ValueError(f"Missing or modified source; preserving local work: {path}")


def main():
    for path in (ROOT / "build", OUTPUT):
        if path.is_symlink():
            raise ValueError(f"Refusing a symlink directory: {path}")
        path.mkdir(exist_ok=True)
    records = []
    for filename, prefix, name, expected in ARCHIVES:
        source = ROOT / filename
        with source.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        if digest != expected:
            raise ValueError(f"Archive changed; inspect before extracting: {filename}")
        with zipfile.ZipFile(source) as archive:
            members = entries(archive, prefix)
            destination = OUTPUT / name
            action = "Verified existing"
            if not os.path.lexists(destination):
                staging = Path(tempfile.mkdtemp(prefix=f".{name}-", dir=OUTPUT))
                try:
                    for info, relative, mode in members:
                        if stat.S_ISLNK(mode):
                            continue
                        path = staging / relative
                        if info.is_dir():
                            path.mkdir(parents=True, exist_ok=True)
                        else:
                            path.parent.mkdir(parents=True, exist_ok=True)
                            path.write_bytes(archive.read(info))
                            path.chmod(0o755 if mode & 0o111 else 0o644)
                    for info, relative, mode in members:
                        if stat.S_ISLNK(mode):
                            path = staging / relative
                            path.parent.mkdir(parents=True, exist_ok=True)
                            path.symlink_to(archive.read(info).decode())
                    verify(archive, members, staging)
                    staging.rename(destination)
                finally:
                    if staging.exists():
                        shutil.rmtree(staging)
                action = "Extracted and verified"
            verify(archive, members, destination)
            records.append({
                "archive": filename, "sha256": digest,
                "archive_comment": archive.comment.decode(),
                "destination": str(destination.relative_to(ROOT)),
                "entries_verified": len(members),
                "symlinks": {str(relative): archive.read(info).decode()
                             for info, relative, mode in members if stat.S_ISLNK(mode)},
            })
            print(f"{action}: {destination.relative_to(ROOT)} ({len(members)} entries)")
    manifest = OUTPUT / "manifest.json"
    content = json.dumps(records, indent=2) + "\n"
    if os.path.lexists(manifest):
        if manifest.is_symlink() or manifest.read_text() != content:
            raise ValueError(f"Preserving an existing different manifest: {manifest}")
    else:
        manifest.write_text(content)


if __name__ == "__main__":
    main()
