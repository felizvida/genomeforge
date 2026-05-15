# Security Model

Genome Forge is designed as a local-first scientific workbench, not as a multi-tenant hosted web service.

## Intended Deployment

- Run on a trusted workstation or trusted lab machine.
- Bind to `127.0.0.1` by default.
- Store project data in repo-local JSON-backed directories.
- Treat all data files, project records, traces, and share bundles as local scientific working files.

The default command is intentionally loopback-only:

```bash
python3 web_ui.py --host 127.0.0.1 --port 8080
```

Avoid binding to `0.0.0.0` unless the machine is behind an appropriate trusted network boundary and you understand that Genome Forge does not yet provide production-grade authentication, session management, rate limiting, or multi-user isolation.

## Browser Boundary

The local HTTP server emits defense-in-depth browser headers on every response:

- `Content-Security-Policy`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: no-referrer`
- `Cross-Origin-Opener-Policy: same-origin`
- `Permissions-Policy` disabling camera, microphone, geolocation, payment, and USB access

The CSP is intentionally strict for scripts:

```text
script-src 'self'
```

Inline scripts and remote scripts are not required for the app shell. Inline styles remain allowed because current share pages and dynamic visual panels still use inline styling; removing that compatibility exception should be a future UI cleanup task.

## Data Trust

Genome Forge accepts user-provided biological data, including FASTA, GenBank-like text, trace payloads, annotations, project names, feature labels, and share metadata. The current hardening posture is:

- generated share HTML escapes stored project metadata and sequence previews
- server-rendered SVG labels escape user-controlled record and feature text
- browser-rendered SVG panels pass through an allowlist sanitizer before DOM insertion
- project ACL updates require an owner actor once initial ownership is established
- audit logs are read-only through the public API surface

## Current Non-Goals

Genome Forge does not currently claim to provide:

- hosted SaaS isolation
- authenticated browser sessions
- encrypted-at-rest project storage
- network-facing access control
- regulated electronic records compliance

Those can be added later, but they require a different deployment architecture than the current lightweight local server.

## Practical Guidance

Use Genome Forge as a local lab workstation app. For collaboration, prefer sharing explicit project bundles, release artifacts, or GitHub issues rather than exposing the local HTTP server to an untrusted network.
