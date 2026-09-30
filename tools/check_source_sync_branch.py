#!/usr/bin/env python3
"""Fail-closed automation scope/ownership check before every push/auto-merge."""
import argparse
import subprocess

from sync_from_sportsbrain import BRANCH, allowed_path, git
from memorylib.v2 import _scan_for_secrets


def check(repo, base="origin/main"):
    if git(repo, "branch", "--show-current") != BRANCH:
        raise ValueError("Unexpected automation branch")
    paths = git(repo, "diff", "--name-only", f"{base}...HEAD").splitlines()
    if not paths or any(not allowed_path(p) for p in paths):
        raise ValueError("Unexpected/empty automation diff")
    if git(repo, "diff", "--diff-filter=D", "--name-only", f"{base}...HEAD"):
        raise ValueError("Automation cannot delete canonical files")
    for sha in git(repo, "rev-list", f"{base}..HEAD").splitlines():
        author = git(repo, "show", "-s", "--format=%ae", sha)
        committer = git(repo, "show", "-s", "--format=%ce", sha)
        subject = git(repo, "show", "-s", "--format=%s", sha)
        if author != "41898282+github-actions[bot]@users.noreply.github.com" or committer != author or subject != "memory: automatic source evidence sync":
            raise ValueError("Non-automation commit present")
    patch = git(repo, "diff", f"{base}...HEAD")
    _scan_for_secrets(patch)
    subprocess.run(["git", "-C", str(repo), "diff", "--check", f"{base}...HEAD"], check=True)
    return paths


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--repo", default=".")
    p.add_argument("--base", default="origin/main")
    a = p.parse_args()
    check(a.repo, a.base)
