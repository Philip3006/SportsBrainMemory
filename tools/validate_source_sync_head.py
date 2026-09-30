"""Normal-token, exact dispatched-run gate before guarded auto-merge."""
import argparse
import json
import re
import subprocess
import time
from pathlib import Path

BRANCH = "automation/sportsbrain-source-sync"


class GateBlocked(RuntimeError):
    pass


def command(*args):
    try:
        return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL, timeout=60).strip()
    except (subprocess.SubprocessError, OSError) as exc:
        raise GateBlocked("VALIDATION_API_ERROR") from exc


def validate_and_merge(repo, pr, head, *, run=command, clock=time.monotonic, sleep=time.sleep, timeout=600):
    dispatch = run("gh", "workflow", "run", "memory-validation.yml", "--repo", repo, "--ref", BRANCH)
    matches = re.findall(r"https://github\.com/" + re.escape(repo) + r"/actions/runs/(\d+)\b", dispatch)
    if len(set(matches)) != 1:
        raise GateBlocked("VALIDATION_RUN_MISSING")
    run_id = matches[0]
    deadline = clock() + timeout
    while clock() < deadline:
        evidence = json.loads(run("gh", "run", "view", run_id, "--repo", repo, "--json",
                                  "databaseId,workflowName,headBranch,headSha,event,status,conclusion"))
        if (str(evidence.get("databaseId")) != run_id or evidence.get("workflowName") != "Memory validation"
                or evidence.get("headBranch") != BRANCH or evidence.get("headSha") != head
                or evidence.get("event") != "workflow_dispatch"):
            raise GateBlocked("VALIDATION_IDENTITY_MISMATCH")
        if evidence.get("status") == "completed":
            if evidence.get("conclusion") != "success":
                raise GateBlocked("VALIDATION_FAILED")
            break
        sleep(min(15, max(0, deadline - clock())))
    else:
        raise GateBlocked("VALIDATION_TIMEOUT")
    if run("gh", "api", f"repos/{repo}", "--jq", ".allow_auto_merge") != "true":
        raise GateBlocked("AUTO_MERGE_BLOCKED")
    if run("gh", "api", f"repos/{repo}/branches/main", "--jq", ".protected") != "true":
        raise GateBlocked("AUTO_MERGE_BLOCKED")
    if run("gh", "pr", "view", pr, "--repo", repo, "--json", "headRefOid", "--jq", ".headRefOid") != head:
        raise GateBlocked("PR_HEAD_MISMATCH")
    try:
        run("gh", "pr", "merge", pr, "--repo", repo, "--auto", "--squash", "--match-head-commit", head)
    except GateBlocked as exc:
        raise GateBlocked("AUTO_MERGE_BLOCKED") from exc
    return run_id


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pr", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--status-output", type=Path, required=True)
    args = parser.parse_args()
    try:
        run_id = validate_and_merge(args.repo, args.pr, args.head)
        print(f"Exact-head Memory validation successful: {run_id}")
    except (GateBlocked, ValueError) as exc:
        status = json.loads(args.status_output.read_text()) if args.status_output.exists() else {}
        reason = str(exc) if isinstance(exc, GateBlocked) else "VALIDATION_API_ERROR"
        status.update(status="SYNC_BLOCKED", failure_reason=reason, validation_status="BLOCKED")
        args.status_output.write_text(json.dumps(status, sort_keys=True) + "\n")
        raise SystemExit(reason)
