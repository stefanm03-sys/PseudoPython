"""Sync .py files between src and docs, then stage both directories.

This keeps runtime files aligned for local execution (src/) and GitHub Pages
execution (docs/). For each top-level ``.py`` file in either directory:
1) If a file exists only on one side, it is copied to the other side.
2) If both exist but differ, the newer file (mtime) overwrites the older one.
3) If both are identical, no action is taken.

Modes:
- src-to-docs (default): one-way copy from src into docs
- docs-to-src: one-way copy from docs into src
- bidirectional: newer file wins in either direction

cd C:/Users/stefa/pseudopy.v0
py -3.12 mirror.py

"""

import argparse
import filecmp
from pathlib import Path
import shutil
import subprocess
import sys


def _copy(src_path: Path, dst_path: Path, note: str) -> None:
    shutil.copy2(src_path, dst_path)
    print(f"  {src_path.parent.name} -> {dst_path.parent.name}  {src_path.name} ({note})")


def stage_docs_assets(root: Path) -> None:
    docs = root / "docs"
    asset_candidates = []
    fixed_files = ["index.html", ".nojekyll"]
    for name in fixed_files:
        p = docs / name
        if p.exists():
            asset_candidates.append(str(p.relative_to(root)))
    for pdf in sorted(docs.glob("*.pdf")):
        asset_candidates.append(str(pdf.relative_to(root)))

    if not asset_candidates:
        print("No docs assets found to stage.")
        return

    subprocess.run(["git", "add", *asset_candidates], check=True, cwd=str(root))
    print("Staged docs assets:", ", ".join(asset_candidates))


def sync_python_files(mode: str = "src-to-docs") -> int:
    root = Path(__file__).parent
    src = root / "src"
    docs = root / "docs"

    if not src.exists():
        print("src directory not found", file=sys.stderr)
        sys.exit(1)
    if not docs.exists():
        print("docs directory not found", file=sys.stderr)
        sys.exit(1)

    src_files = {p.name: p for p in src.iterdir() if p.is_file() and p.suffix == ".py"}
    docs_files = {p.name: p for p in docs.iterdir() if p.is_file() and p.suffix == ".py"}
    all_names = sorted(set(src_files) | set(docs_files))

    print(f"Syncing top-level .py files between {src} and {docs} (mode: {mode})...")
    changes = 0

    for name in all_names:
        src_path = src_files.get(name)
        docs_path = docs_files.get(name)

        if mode == "src-to-docs":
            if src_path and not docs_path:
                _copy(src_path, docs / name, "created in docs")
                changes += 1
            elif src_path and docs_path and not filecmp.cmp(src_path, docs_path, shallow=False):
                _copy(src_path, docs_path, "updated from src")
                changes += 1
            continue

        if mode == "docs-to-src":
            if docs_path and not src_path:
                _copy(docs_path, src / name, "created in src")
                changes += 1
            elif src_path and docs_path and not filecmp.cmp(src_path, docs_path, shallow=False):
                _copy(docs_path, src_path, "updated from docs")
                changes += 1
            continue

        # bidirectional mode
        if src_path and not docs_path:
            _copy(src_path, docs / name, "created in docs")
            changes += 1
            continue

        if docs_path and not src_path:
            _copy(docs_path, src / name, "created in src")
            changes += 1
            continue

        if src_path is None or docs_path is None:
            continue

        if filecmp.cmp(src_path, docs_path, shallow=False):
            continue

        src_mtime = src_path.stat().st_mtime
        docs_mtime = docs_path.stat().st_mtime
        if src_mtime >= docs_mtime:
            _copy(src_path, docs_path, "newer in src")
        else:
            _copy(docs_path, src_path, "newer in docs")
        changes += 1

    if changes == 0:
        print("No .py sync changes needed.")

    try:
        subprocess.run(["git", "add", "src", "docs"], check=True, cwd=str(root))
        stage_docs_assets(root)
        print("Staged src and docs for commit.")
    except subprocess.CalledProcessError as exc:
        print("Failed to run git add:", exc, file=sys.stderr)
        sys.exit(1)

    return changes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync top-level .py files between src and docs.")
    parser.add_argument(
        "--mode",
        choices=["src-to-docs", "docs-to-src", "bidirectional"],
        default="src-to-docs",
        help="sync direction/mode (default: src-to-docs)",
    )
    args = parser.parse_args()
    sync_python_files(mode=args.mode)
