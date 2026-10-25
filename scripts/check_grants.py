#!/usr/bin/env python3
"""Print every grant in a Kortix project as a table, and flag the wide defaults.

Reads the project manifest (kortix.yaml) and reports, per agent: its file, what
it may reach, whether it names its tools, and whether it holds `all` on a
deny-by-default key. Runs on a commit, not on a running project, so it can gate
a change request in CI.

    python3 scripts/check_grants.py kortix.yaml
    python3 scripts/check_grants.py kortix.yaml --strict   # exit 1 on findings
    python3 scripts/check_grants.py kortix.yaml --json

Findings are graded:
    HIGH  a grant a reviewer will hold the project for (an agent with every
          tool, an agent holding `all` on connectors/secrets/apps/permissions)
    LOW   worth naming, not a block (an omitted policy mode, a missing policy)
"""

from __future__ import annotations

import argparse
import json
import os
import sys

try:
    import yaml
except ImportError:  # pragma: no cover - the message is the point
    sys.exit("check_grants.py needs PyYAML: pip install pyyaml")

# The grants that are deny-by-default when the key is omitted.
DENY_BY_DEFAULT = ("connectors", "secrets", "apps", "kortix_permissions")
ALL_VALUES = {"all", "*"}
LABELS = {"connectors": "connector", "secrets": "secret", "apps": "App",
          "kortix_permissions": "Kortix permission", "tools": "tool"}


def load(path: str) -> dict:
    with open(path, encoding="utf-8") as handle:
        doc = yaml.safe_load(handle) or {}
    if not isinstance(doc, dict):
        raise SystemExit(f"{path}: not a mapping at the top level")
    return doc


def is_all(value) -> bool:
    """`all`, `"*"`, or a list that contains either."""
    if isinstance(value, str):
        return value.strip().lower() in ALL_VALUES
    if isinstance(value, (list, tuple)):
        return any(isinstance(v, str) and v.strip().lower() in ALL_VALUES
                   for v in value)
    return False


def describe(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value) or "none"
    if isinstance(value, dict):
        if "exclude" in value:
            excluded = value.get("exclude") or []
            return "all but " + (", ".join(map(str, excluded)) or "none")
        return json.dumps(value, sort_keys=True)
    return str(value)


def check(doc: dict, base: str) -> tuple[list[dict], list[dict]]:
    agents = doc.get("agents") or {}
    if not isinstance(agents, dict) or not agents:
        raise SystemExit("manifest declares no agents")

    rows, findings = [], []
    for name, block in agents.items():
        block = block if isinstance(block, dict) else {}
        agent_file = block.get("file") or f"agents/{name}.md"
        row = {"agent": name, "file": agent_file}
        for key in DENY_BY_DEFAULT:
            row[key] = describe(block.get(key))
        row["skills"] = describe(block.get("skills"))
        row["tools"] = describe(block.get("tools"))
        rows.append(row)

        if not os.path.exists(os.path.join(base, agent_file)):
            findings.append({
                "severity": "HIGH", "agent": name,
                "finding": f"file {agent_file!r} does not exist",
            })
        if block.get("tools") is None:
            findings.append({
                "severity": "HIGH", "agent": name,
                "finding": "no `tools` key: the agent inherits every tool",
            })
        for key in DENY_BY_DEFAULT:
            if is_all(block.get(key)):
                findings.append({
                    "severity": "HIGH", "agent": name,
                    "finding": f"`{key}: all`: the agent holds every {LABELS.get(key, key)}",
                })
        if block.get("enabled") is False:
            findings.append({
                "severity": "LOW", "agent": name,
                "finding": "`enabled: false`: no session can start it",
            })

    default_agent = doc.get("default_agent")
    if not default_agent:
        findings.append({"severity": "HIGH", "agent": "-",
                         "finding": "no `default_agent` in the manifest"})
    elif default_agent not in agents:
        findings.append({"severity": "HIGH", "agent": "-",
                         "finding": f"`default_agent: {default_agent}` names no declared agent"})
    elif (agents.get(default_agent) or {}).get("enabled") is False:
        findings.append({"severity": "HIGH", "agent": default_agent,
                         "finding": "the default agent is disabled"})

    policy = doc.get("policy") or {}
    mode = policy.get("default_mode") if isinstance(policy, dict) else None
    if mode not in ("allow_all", "risk"):
        findings.append({
            "severity": "LOW", "agent": "-",
            "finding": f"`policy.default_mode` is {mode!r}: Kortix falls back to allow_all",
        })
    elif mode == "allow_all":
        findings.append({
            "severity": "LOW", "agent": "-",
            "finding": "`policy.default_mode: allow_all`: no unmatched call waits for a person",
        })
    return rows, findings


def table(rows: list[dict]) -> str:
    columns = ["agent", "connectors", "secrets", "apps", "kortix_permissions",
               "skills", "tools", "file"]
    widths = {c: max(len(c), *(len(str(r.get(c, "-"))) for r in rows)) for c in columns}
    head = "  ".join(c.ljust(widths[c]) for c in columns)
    rule = "  ".join("-" * widths[c] for c in columns)
    body = ["  ".join(str(r.get(c, "-")).ljust(widths[c]) for c in columns) for r in rows]
    return "\n".join([head, rule, *body])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", nargs="?", default="kortix.yaml")
    parser.add_argument("--strict", action="store_true",
                        help="exit non-zero when a HIGH finding is present")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args()

    doc = load(args.manifest)
    base = os.path.dirname(os.path.abspath(args.manifest))
    rows, findings = check(doc, base)

    policy = doc.get("policy") or {}
    mode = policy.get("default_mode", "allow_all") if isinstance(policy, dict) else "allow_all"
    ttl = (doc.get("approvals") or {}).get("ttl", "24h") if isinstance(doc.get("approvals"), dict) else "24h"

    if args.json:
        print(json.dumps({
            "manifest": args.manifest,
            "kortix_version": doc.get("kortix_version"),
            "default_agent": doc.get("default_agent"),
            "policy_default_mode": mode,
            "approvals_ttl": ttl,
            "agents": rows,
            "findings": findings,
        }, indent=2))
    else:
        print(f"{args.manifest}: kortix_version {doc.get('kortix_version')}, "
              f"default agent {doc.get('default_agent')}, "
              f"policy {mode}, approvals ttl {ttl}\n")
        print(table(rows))
        print()
        if findings:
            for finding in findings:
                print(f"{finding['severity']:<5} {finding['agent']:<18} {finding['finding']}")
        else:
            print("no findings")

    high = [f for f in findings if f["severity"] == "HIGH"]
    return 1 if (args.strict and high) else 0


if __name__ == "__main__":
    sys.exit(main())
