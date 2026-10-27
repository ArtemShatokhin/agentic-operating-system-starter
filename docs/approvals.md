# Approvals in an open-source Kortix project: which calls wait for a person

A policy decides what happens when a connector action is called: Allow (`always_run`), Ask
(`require_approval`) or Block (`block`). Kortix evaluates in this order and the first match wins:

1. Project-wide `policies:` in `kortix.yaml`. Patterns are fully qualified (`billing.refund_payment`,
   `*.*delete*`). A connector's own rule cannot override them.
2. The connector's own `policies:`. Patterns are relative to the connector (`refund_*`).
3. `sensitive: true` on the connector: every remaining action needs approval, reads included.
4. `policy.default_mode`: `allow_all` runs every remaining action; `risk` runs reads and holds writes and
   destructive calls.

`allow_all` is the default, which is why a fresh project runs every action its grants allow. Set
`policy.default_mode: risk` in any project whose agents touch money, mail, tickets or production. These rules travel with the project, and [the three questions that settle which of the two you need](https://agenticoperatingsystemguide.com/agentic-operating-system-vs-orchestration-platforms) put a committed policy beside a platform that decides which agent runs next.

This project's rules hold every payment and every refund for a person, and block every delete, whatever a
connector answers:

```yaml
policy:
  default_mode: risk

policies:
  - match: "*.*refund*"
    action: require_approval
  - match: "*.*payment*"
    action: require_approval
  - match: "*.*delete*"
    action: block
```

A rule can also test the call's arguments, with one or more `conditions` that must all hold (`negate: true`
inverts one). The manifest reference's own example, with `gmail.send_email` as the fully qualified action:

```yaml
policies:
  - match: gmail.send_email
    action: require_approval
    conditions:
      - arg: to
        match: "*@example.com"
  - match: gmail.send_email
    action: block
```

A malformed condition fails closed: it never opens an action. `kortix validate` does not check `policy` or
`policies`, so read the connector settings after a merge; a malformed rule is skipped at connector sync and
reported as a sync error.

## What a held call returns

A held call returns `202` with `status: "pending_approval"`, an `approval_url`, a summary and an execution
id. Nothing ran. A person opens it in Review, through the URL, or on the approval card in a Slack or Teams
thread, and the page asks for a signed-in account that can approve actions in the project.

One approval covers one exact request: same connector, same action, same arguments, same account. Change
an argument and the call needs a new approval. There is no session-wide approval, so any action that must
run unattended needs an `always_run` rule for that exact action. That cost belongs in the deployment plan,
not in a footnote.

## Expiry

A held call waits 24 hours unless the project sets `approvals.ttl`:

```yaml
approvals:
  ttl: 4h
```

The value is an integer and `m`, `h` or `d`, clamped to five minutes through 30 days. This project uses
four hours. When nobody decides in time the call leaves Review, its card shows Expired, a POST to the
approval returns `409` with `APPROVAL_EXPIRED`, and the session does not resume: the agent asks again with
a new call.

## Inside the machine

The approval policy governs connector calls. The agent file's `permission` block governs harness tools and
takes `allow`, `ask` or `deny` per tool, or per pattern: `bash: { "*": ask, "git diff *": allow }`. The
most specific matching pattern wins. A `bash` pattern that asks waits for a person the same way a
connector call does. `support-triage.md` has no shell at all, and `release-check.md` allows six read-only
commands and denies the rest.

## Audit

Every action is recorded, with the action in `domain.resource.verb` form, the actor, the credential and the
outcome. A row keeps the route template rather than the raw path, because a path segment can be an
approval link. Recording is always on; reading, exporting and streaming the log depend on the plan, and
`auditAccess` is an Enterprise entitlement. Price that before promising an auditor a live feed. A log names
an identity, not a person: a sandbox or a script holding someone's token writes rows as that person.
