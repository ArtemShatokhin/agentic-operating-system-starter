# Grants in an open-source Kortix project: what each agent may touch, and who can widen it

An agent is two halves. Behavior (prompt, model, mode, `permission` rules for its tools) lives in
`agents/<name>.md`. Governance (connectors, secrets, apps, skills, Kortix permissions, tools) lives in
the `agents.<name>` block in `kortix.yaml`. In a v2 project the block rejects a behavior key; the
manifest is the grant, the file is the job.

## The six grants

| Grant | Lists | Omitted | What it unlocks |
| --- | --- | --- | --- |
| `connectors` | connector slugs | none | Calls to those connectors, through the brokered credential |
| `secrets` | secret identifiers | none | Those secrets in the sandbox and through the secrets API |
| `apps` | App slugs | none | Opening those Apps when their access is restricted |
| `kortix_permissions` | `project.*` entries | none | Kortix CLI, API and git actions |
| `skills` | skill names | the agent file's `permission.skill` decides | Loading those skills |
| `tools` | tool names, or `exclude: [...]` | every tool | Harness, Kortix and project tools |

Four are deny-by-default. Two are not, and those two decide the width of a review:

- `tools` omitted grants every tool, which is the widest default in the file. Every agent in this repo
  names `tools` for that reason.
- `skills` omitted means the agent file decides, and a bare `permission: allow` allows every skill.

An agent that names `all` or `"*"` on any of the four deny-by-default keys holds every connector, every
secret, every App or every project permission in the project. The starter project Kortix ships does this
for its own default agent on purpose, so a fresh project can do work immediately. That block is the first
thing to narrow, and because it sits in the same file as everything else, narrowing it shows up as a diff.

## Check a permission name before you use it

`kortix validate --scopes` prints every grantable permission entry with its aliases. A name that is not on
that list fails `kortix validate` and fails a change request merge; at runtime Kortix ignores it and
applies the rest, which is the worst of both outcomes. Examples of names that do exist:
`project.session.read`, `project.review.submit`, `project.gitops.read`, `project.gitops.merge`,
`project.agent.write`, `project.secret.read`, `project.file.write`.

## Who may widen a grant

Widening a grant is a commit to `kortix.yaml`. Four rules govern the commit:

1. Merging a change request needs `project.gitops.merge`.
2. A merge that changes `agents` or `default_agent` also needs `project.agent.write`.
3. An agent grants only what it holds. When an agent session writes a grant, every permission, connector,
   secret and App it adds must already be in its own effective grant. Narrowing is always allowed.
4. A session pushes only its own branch unless its agent holds `project.gitops.ref.any`.

An agent's effective permissions are its `kortix_permissions` intersected with the ceiling role bound to it
in the account, minus the human-only permission. The ceiling never adds a permission. No agent holds
`project.credentials.issue`: minting a project credential stays with people.

A config edit from the dashboard can commit straight to the default branch, so a review that names only
repository writers misses a route. Both kinds of change leave audit rows, `agent.config.update` and
`agent.scope.update`.

## Who may run an agent

The person who runs an agent lends it no authority, so the right to run it is the delegation. Account
owners and admins may run every agent; a project manager may run unassigned agents and the agents assigned
to them or their groups; a project member may run the agents assigned to them or to the whole project. A
person with no agent grant gets a 403 when a session starts.

Two grants therefore line up before an agent works for someone: the agent's grant decides what it may
reach, and the person's grant decides whether they can start it.

## Reading a denial

A refused call answers `403` with a `code` and the `action` it checked. `agent_scope_insufficient` means
the action is missing from the agent's `kortix_permissions`: add it and merge. `agent_ceiling_insufficient`
means the action is outside the role bound to the agent: an account admin raises the role, and editing the
manifest will not help. `agent_grant_escalation` means an agent's write tried to hand out something the
writing agent does not hold.
