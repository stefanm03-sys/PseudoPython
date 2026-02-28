"""Mirror source files into docs and stage them for commit.

Run this from the repository root whenever you edit code in ``src/`` and want
those changes reflected in the GitHub Pages copy under ``docs/``.  The script
copies every ``.py`` file from ``src/`` into ``docs/`` (overwriting), then
runs ``git add docs`` so the updated files are staged.

It does **not** commit for you so you can review or add a custom message.
"""

from pathlib import Path
import shutil
import subprocess
import sys

def mirror_sources():
    root = Path(__file__).parent
    src = root / "src"
    docs = root / "docs"

    if not src.exists():
        print("src directory not found", file=sys.stderr)
        sys.exit(1)
    if not docs.exists():
        print("docs directory not found", file=sys.stderr)
        sys.exit(1)

    print(f"Mirroring *.py from {src} to {docs}...")
    for path in src.iterdir():
        if path.suffix == ".py":
            dest = docs / path.name
            shutil.copy2(path, dest)
            print(f"  copied {path.name}")

    # stage changes with git
    try:
        subprocess.run(["git", "add", "docs"], check=True, cwd=str(root))
        print("Staged docs directory for commit.")
    except subprocess.CalledProcessError as exc:
        print("Failed to run git add:", exc, file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    mirror_sources()