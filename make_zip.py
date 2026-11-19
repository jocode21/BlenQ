#!/usr/bin/env python3
"""Build BlenQ_v1.zip from ~/workspace/blender-generator.

One top folder (BlenQ_v1). Excludes caches, the trained model
(data/model.pt is created by training and must never ship), and
any stray artefacts. Prints the file list, size and SHA-256.
"""
import hashlib
import os
import shutil
import sys
import zipfile

SRC = os.path.expanduser("~/workspace/blender-generator")
OUT_DIR = os.path.expanduser("~/workspace/your_files/blender-generator")
OUT = os.path.join(OUT_DIR, "BlenQ_v1.zip")

EXCLUDE_DIRS = {"__pycache__", ".pytest_cache", ".venv", "venv", ".git"}
EXCLUDE_FILES = {"model.pt", "history.json", "last_render.png", ".coverage"}
EXCLUDE_SUFFIXES = (".pyc", ".blend", ".blend1")


def keep(path, name):
    rel = os.path.relpath(path, SRC)
    parts = rel.split(os.sep)
    if any(p in EXCLUDE_DIRS for p in parts):
        return False
    if name in EXCLUDE_FILES:
        return False
    if name.endswith(EXCLUDE_SUFFIXES):
        return False
    return True


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    files = []
    for root, dirs, names in os.walk(SRC):
        dirs[:] = [d for d in dirs
                   if os.path.join(root, d) not in EXCLUDE_DIRS
                   and d not in EXCLUDE_DIRS]
        for n in sorted(names):
            p = os.path.join(root, n)
            if keep(p, n):
                files.append(p)
    files.sort()
    if os.path.exists(OUT):
        os.remove(OUT)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            rel = os.path.relpath(p, SRC)
            z.write(p, os.path.join("BlenQ_v1", rel))
    h = hashlib.sha256()
    with open(OUT, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    print(f"files: {len(files)}")
    print(f"zip:   {OUT}")
    print(f"bytes: {os.path.getsize(OUT):,}")
    print(f"sha256: {h.hexdigest()}")
    for p in files:
        print("  " + os.path.relpath(p, SRC))


if __name__ == "__main__":
    main()
