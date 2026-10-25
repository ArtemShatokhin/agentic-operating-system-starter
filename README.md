# Agentic OS starter: a deny-by-default, open-source Kortix project

A small, working Kortix project you can read in one sitting: one committed `kortix.yaml`, three
specialist agents, the approval policy that holds a payment until a person signs it, and a script that
prints every grant in the project as a table.

Kortix is the open-source AI Operating System: your agents, their skills, your company memory and every
connector in one git repo you own. This repo is the smallest honest example of the part that matters to a
security reviewer, which is the governance half. An agentic operating system decides what each agent may
reach, on which machine, and who approves a consequential call. Here those decisions are files, and the
diff is the review.

Written to accompany [agenticoperatingsystemguide.com](https://agenticoperatingsystemguide.com), which
explains the category and what a security review of it looks for.

## What is in here

| Path | What it shows |
| --- | --- |
| `kortix.yaml` | The manifest: three agents, per-agent grants, the project-wide approval policy |
| `agents/ops-readout.md` | A reporting agent that reads two connectors and writes a file |
| `agents/support-triage.md` | A triage agent with one connector, no write tool, and a shell that always asks |
| `agents/release-check.md` | A read-only agent: no connectors, no secrets, no git merge |
| `docs/grants.md` | The four deny-by-default keys, and the two keys that are not |
| `docs/approvals.md` | Allow, Ask, Block; the approval window; what a held call returns |
| `docs/security-review-checklist.md` | The questions to answer before a demo, as a checklist |
| `docs/self-hosting.md` | What changes when you run it on your own network |
| `scripts/check_grants.py` | Prints every agent's effective grant and flags the wide defaults |

## Read the manifest first

The three agents are deliberately narrow. Grants are deny-by-default in a v2 manifest: an agent with no
`connectors`, `secrets`, `apps` or `kortix_permissions` key gets none of them. Two keys differ. An omitted
`tools` key grants every tool, which is the widest default in the file, and an omitted `skills` key leaves
skill access to the agent file's own `permission` rules. Every agent here names `tools` explicitly for
that reason.

```yaml
agents:
  support-triage:
    file: agents/support-triage.md
    connectors: [helpdesk]
    secrets: [HELPDESK_API_KEY]
    skills: [kortix-cli]
    kortix_permissions: [project.session.read, project.review.submit]
    tools: [read, grep, web_search, scrape_webpage, memory]
```

That block is the whole answer to "what may this agent touch": one connector, one secret, five tools, and
two project permissions. A person who widens it does it in a commit.

## Check the grants

```bash
pip install pyyaml          # the only dependency, and only for the checker
python3 scripts/check_grants.py kortix.yaml
```

It prints one row per agent, the policy mode in force, and a list of findings such as an agent that
inherits every tool, an agent granted `all`, or an `agents.<name>.file` that does not exist. `--strict`
exits non-zero on the findings a reviewer would hold the project for. It reads the manifest, not the
running project, so it runs in CI on the same commit the reviewer reads.

## Run it

The manifest is a real Kortix project, not a sketch. To try it:

```bash
kortix init                       # set the project up in a local checkout
kortix validate                   # schema and grant names
kortix validate --scopes          # every grantable permission entry, with aliases
kortix agents ls                  # each agent, its file and its model
kortix connectors policy ls       # the project-wide rules
```

`kortix validate --scopes` is the part to run before you accept a grant name from anyone, including from
this repo: it prints the list the platform enforces, so a name is checked rather than guessed.

## The four questions this repo answers

1. **What may each agent touch?** The `agents.<name>` blocks in `kortix.yaml`.
2. **Who may widen that?** A commit to `kortix.yaml`, governed by `project.agent.write` and the account
   roles. See `docs/grants.md`.
3. **Who approves a consequential action?** The `policy` and `policies` entries, plus each connector's own
   rules and its `sensitive` flag. See `docs/approvals.md`.
4. **Where is the record?** The audit log, which keeps `domain.resource.verb`, the actor and the
   credential for every action. See `docs/security-review-checklist.md` for its limits.

## Links

- [What an agentic operating system is](https://agenticoperatingsystemguide.com/what-is-an-agentic-operating-system)
- [What a security reviewer checks](https://agenticoperatingsystemguide.com/agentic-operating-system-permissions-and-approvals)
- [Self-hosting the same manifest](https://agenticoperatingsystemguide.com/self-hosted-agentic-operating-system)
- [Kortix docs: agents and permissions](https://kortix.com/docs/project/agents)
- [Kortix docs: connectors, policies and approvals](https://kortix.com/docs/connect/connectors)
- [Kortix on GitHub](https://github.com/kortix-ai/suna)

The manifest shape, the grant keys and the policy keys are the platform's own, checked against the
`kortix.yaml` reference and the connectors reference on 2026-10-25. The three agents, the docs and the
checker are written for this repo. Nothing here is a fork of the platform.
