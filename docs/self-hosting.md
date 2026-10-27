# Self-hosting an open-source Kortix project: what changes

The manifest, the change-request path and the audit log travel with the instance. Self-hosting moves where
the control plane and the sessions run; it does not change the grant model or the approval model, which are
the parts a review reads. What does change sits on the host, and [the reachability mode that decides whether sessions start](https://agenticoperatingsystemguide.com/self-hosted-agentic-operating-system) is the first setting to settle.

- **The same `kortix.yaml`.** This repo is the project. Check it out on the instance and it behaves as it
  did in the cloud: the same agent blocks, the same `permissions`, the same `policies`.
- **Your own network.** The instance can be reached on a private network, behind a VPN, or on a machine
  with no inbound route at all. The three reachability modes and the first-boot sequence are in
  [the hosting docs](https://kortix.com/docs/host).
- **Your own keys.** A self-hosted project runs on the provider keys you configure, or on your own
  OpenAI-compatible endpoint. Managed models are a cloud-plan feature; on a self-hosted instance the model
  access, and its bill, are yours.
- **Your own database and storage.** Sessions, the audit log and project data land in the database you
  point the instance at, so backup, retention and residency are yours to set.
- **The audit entitlement.** The audit log is always recorded. Reading, exporting and streaming it are
  gated by the plan on a cloud account; on a self-hosted instance you set that up yourself.

Nothing in this repo assumes the cloud. The script reads a file and prints a table.
