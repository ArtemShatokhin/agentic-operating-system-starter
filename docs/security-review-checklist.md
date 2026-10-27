# Security review checklist for an open-source agentic operating system

Answer these before the demo, with the file or the screen that answers each one. The order is the order a
reviewer asks them. [The four questions a review answers from one manifest](https://agenticoperatingsystemguide.com/agentic-operating-system-permissions-and-approvals) walks the same order against a committed `kortix.yaml`.

## 1. What may each agent touch?

- [ ] Every agent has an `agents.<name>` block in `kortix.yaml`, and the block names `connectors`,
      `secrets`, `apps` and `kortix_permissions` explicitly.
- [ ] No agent inherits `tools`. An omitted `tools` key grants every tool.
- [ ] No agent holds `all` or `*` on a deny-by-default key unless the change request says why.
- [ ] `python3 scripts/check_grants.py kortix.yaml --strict` exits zero on the release commit.

## 2. Who may widen a grant?

- [ ] Merging a change request needs `project.gitops.merge`; a merge touching `agents` also needs
      `project.agent.write`.
- [ ] No agent holds `project.gitops.ref.any` without a written reason.
- [ ] No agent holds `project.credentials.issue`; that permission is human-only by design.
- [ ] The review names who can commit a config edit from the dashboard, as well as who holds repository
      write.
- [ ] The role ceiling bound to each agent is recorded, because the ceiling, not the manifest, is the
      outer bound on what an agent can do.

## 3. Who approves a consequential action?

- [ ] `policy.default_mode` is `risk` for any project whose agents touch money, mail, tickets or
      production.
- [ ] Every unattended action that has to run has an `always_run` rule for that exact action, and nothing
      wider. There is no session-wide approval.
- [ ] Every connector that can move money or data has a `policies` entry or `sensitive: true`.
- [ ] `approvals.ttl` is short enough for the job. A held call waits 24 hours by default.
- [ ] The people who can approve are named, and they are not the agent's own launcher where the action is
      consequential.

## 4. Where is the record?

- [ ] The audit log is on. Recording is always on; reading it may need the Enterprise `auditAccess`
      entitlement, so check the plan before the audit.
- [ ] The audit keeps `domain.resource.verb`, the actor type, the credential kind and the outcome, and it
      names the person an agent acted for.
- [ ] The limits are written down: a log names an identity, not a person, and it cannot show intent.
- [ ] Secret exposure is understood. A granted secret arrives in the sandbox as an environment value that
      any command there can read, so rotation belongs in the runbook.
- [ ] The session boundary is understood. Each session gets its own isolated machine and its own branch, so
      only what a session commits and pushes survives.

## 5. What reaches production?

- [ ] Session work reaches the default branch through a change request.
- [ ] Merge is default-deny for agents: an agent merges only with `project.gitops.merge`, and a session
      that opened a change request cannot merge it without that grant.
- [ ] The merging agent cannot grant a permission it does not hold. That chain is the reason the agent
      which benefits from a wider grant cannot approve one.
