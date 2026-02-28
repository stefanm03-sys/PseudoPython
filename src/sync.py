# sync.py
import subprocess
import sys
from pathlib import Path

GIT = Path("Git/mingw64/bin/git.exe")  # adjust if git is on PATH

def run(*args):
    print("$", *args)
    subprocess.check_call([str(GIT), *args])

def main():
    # make sure we’re in project root
    repo = Path(__file__).parent
    run("pull")
    run("add", ".")
    run("commit", "-m", "automatic sync")
    run("push")

if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print("git failed:", e)
        sys.exit(1)