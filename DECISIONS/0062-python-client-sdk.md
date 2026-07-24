# 0062 — Python Client SDK

## Context

The Doctrine's Interface layer names a *Python API Proxy* alongside the
verification terminal — a programmatic way in. But the platform shipped only the
HTTP API and a browser console; a Python consumer had to hand-roll `requests`
calls, remember endpoint paths, thread the bearer token through every header, and
parse errors themselves. A verification service that expects to be embedded in
other people's pipelines needs a client, not just a wire protocol.

## Decision

Ship a thin Python client, `oceanicos_client.OceanicOSClient`.

- It wraps the platform's endpoints in a small, named surface — `cvi()`,
  `status()`, `status_digest()`, `evolution()`, `doctrine()`, `verify()`,
  `stats()`, `receipt()`, `subject_history()`, `lookup()`, `consensus()`,
  `attention()` — with `register()` capturing and storing the bearer token so
  authed calls just work.
- The **transport is injectable**: an `opener(method, path, headers, json)`
  callable. The default speaks real HTTP via `requests`; a test (or an in-process
  caller) passes an opener backed by the Flask test client. So the client is
  exercised against the *real* routes and cannot drift from them.
- Non-2xx responses raise `OceanicOSError` carrying the status and body, so a
  consumer gets a real exception with the platform's own error message rather than
  a silent bad payload.

## Consequences

- The platform is now consumable in a few lines, and the client is proven against
  the live API two ways: the test suite drives every method through the Flask
  test-client opener, and a live run against `gunicorn` over real HTTP reads
  `posture TRUSTWORTHY`, the CVI, the compounding footprint, registers a token,
  and convenes the panel — the default `requests` transport and the injected one
  both work.
- The injectable opener is the key design choice: it means the SDK has no
  hermeticity problem in tests (no network, no live server needed) while still
  exercising the actual route handlers, so a renamed endpoint or changed response
  shape breaks the client's tests — the client and the API are wired together, not
  merely adjacent.
- Lazy `requests` import keeps the module importable where `requests` is absent
  (an in-process caller injecting its own opener never needs it), so the client is
  usable both as a network SDK and as a typed in-process facade.
- Honest scope: this realizes the *Python API Proxy* interface node. The Doctrine's
  other named interfaces — the Tampermonkey web injector and the `kai.sh` terminal
  — remain client-side artifacts outside this repository, and are not claimed here.
