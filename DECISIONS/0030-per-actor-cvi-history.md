# 0030 — Per-Actor CVI History

## Context

Round 19 (DECISIONS/0023) recorded the CVI as a time series, but only the
platform-wide one (`actor=''`). The personal surface — `/me/builds`,
`/me/attestations`, `/me/cvi`, `/me/quota`, `/me/usage` — could show an actor
their *current* verification quality but not its trend. An account can't see
whether its own work is improving, which is the same gap the platform trend
closed, one level down.

## Decision

Record and expose a per-actor CVI trend.

- `_snapshot_cvi(actor=None)` now records the platform snapshot as before and,
  when a named actor drove the change, that actor's scoped snapshot too
  (`cvi_history` already keyed series by actor). It is called with `g.actor` from
  the build path; the held-review path stays platform-only, because a release
  moves the *attestation owner's* and platform's quality, not the reviewing
  admin's.
- `GET /me/cvi/history` (`?limit=`) returns the authenticated actor's own series,
  completing the `/me/*` surface.

## Consequences

- An account can watch its own verification quality over time: verified live —
  after two builds, `/me/cvi/history` returns `alice`'s series whose latest point
  equals `/me/cvi`.
- No new store and no new recording path: it reuses `cvi_history`'s existing
  actor scoping and the same change-only rule (round 19), so the personal series
  is as bounded and meaningful as the platform one. The only change is passing
  the actor at the build call site.
- Snapshotting is deliberately scoped to who actually caused the change. The
  build path attributes to the builder; the held-review path does not attribute
  to the reviewer, since the reviewer's own CVI didn't move — mis-attributing it
  would pollute a steward's trend with other people's releases.
- The `/me/*` surface is now symmetric with the global one (`/cvi` ↔
  `/me/cvi`, `/cvi/history` ↔ `/me/cvi/history`), so scoping stays a consistent
  lens: the same data, filtered to the caller.
