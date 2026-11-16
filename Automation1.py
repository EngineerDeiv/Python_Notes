#!/usr/bin/env python3
"""
git_autocommit.py

Step 1: new/modified files -> commit "Adding notes YYYY-MM-DD" -> push
Step 2: deleted files      -> commit "deleted notes YYYY-MM-DD" -> push

Usage:
    python git_autocommit.py                  # current folder, current branch
    python git_autocommit.py -b main          # specific branch
    python git_autocommit.py -r ~/my-notes    # specific repo path
    
To execute in the Shell/Bash/CMD/:

use this command TO RUN just 1 time the script:
    python Automation1.py
    
use this command to put a time that the script will run and will stop when you press CTRL + C
    while true; do python Automation1.py; sleep 10; done

"""
import argparse
import subprocess
import sys
from datetime import date


def run_git(args, repo, show_output=False):
    """Run a git command. Stop the script if it fails."""
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] git {' '.join(args)}")
        print(result.stderr.strip())
        sys.exit(result.returncode)
    if show_output:
        # git push writes its progress to stderr, so print both
        output = (result.stdout + result.stderr).strip()
        if output:
            print(output)
    return result.stdout


def get_status_codes(repo):
    """Return the 2-char XY codes from 'git status --porcelain'."""
    output = run_git(["status", "--porcelain"], repo)
    return [line[:2] for line in output.splitlines() if line]


def has_new_or_modified(codes):
    # ?? = untracked, M = modified, A = added, R = renamed, C = copied, T = type change
    return any(code == "??" or any(c in "MARCT" for c in code) for code in codes)


def has_deleted(codes):
    return any("D" in code for code in codes)


def commit_and_push(repo, message, branch):
    # 'git diff --cached --quiet' returns 0 when nothing is staged
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=repo)
    if staged.returncode == 0:
        print("Nothing staged, skipping commit.")
    else:
        run_git(["commit", "-m", message], repo, show_output=True)
        run_git(["push", "origin", branch], repo, show_output=True)
        print(f"[OK] '{message}' pushed to origin/{branch}")


def main():
    parser = argparse.ArgumentParser(description="Auto commit and push notes")
    parser.add_argument("-r", "--repo", default=".", help="Path to the git repo")
    parser.add_argument("-b", "--branch", help="Branch to push (default: current)")
    args = parser.parse_args()

    # Always work from the repo root so '.' covers the whole repo
    repo = run_git(["rev-parse", "--show-toplevel"], args.repo).strip()

    if args.branch:
        branch = args.branch
    else:
        branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"], repo).strip()

    if branch == "HEAD":
        print("[ERROR] Detached HEAD. Use -b <branch_name>.")
        sys.exit(1)

    today = date.today().isoformat()  # e.g. 2026-11-02
    print(f"Repo: {repo} | Branch: {branch} | Date: {today}\n")

    # ---------- Step 1: new / modified files ----------
    print("== Step 1: new/modified files ==")
    codes = get_status_codes(repo)
    if has_new_or_modified(codes):
        # Stage new + modified files, but NOT deletions
        run_git(["add", "--ignore-removal", "."], repo)
        commit_and_push(repo, f"Adding notes {today}", branch)
    else:
        print("No new or modified files.")

    # ---------- Step 2: deleted files ----------
    print("\n== Step 2: deleted files ==")
    codes = get_status_codes(repo)
    if has_deleted(codes):
        # Stage changes to tracked files only (here, the remaining deletions)
        run_git(["add", "--update", "."], repo)
        commit_and_push(repo, f"deleted notes {today}", branch)
    else:
        print("No deleted files.")


if __name__ == "__main__":
    main()