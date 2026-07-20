# 0015 — Boot Manifest and the Anchor of Last Resort

## Context

The OceanicOS "Full-Stack Vibe Protocol" had lived only as prose — a directive
passed between operator and system. Its invocation, `oceanic-os --boot
/boot/init.v1 --state stateless --exit 0`, named a manifest and a CLI that did
not exist, and a "fallback cache" — an Anchor of Last Resort — that had never
been written. Meanwhile most of the manifest was already true in code; it simply
had no single artifact that ratified it or a way to boot from it. This round
makes the manifest executable and gives the platform its floor of degradation.

## Decision

### The manifest is a ratified, hash-attested artifact
`boot/init.v1` is the manifest as parseable JSON, committed to the repo.
`/observer` and the boot CLI report its sha256, so the manifest attests to itself
the way the Constitution already does. Most of its fields map to existing code
(threshold `0.74` → `CONFIDENCE_THRESHOLD`; `parallelism 3` +
`PRIMARY_OUTPUT` → `ModelRouter.route_all(panel=3)` and the verdict strategies;
`Degrade_to_Spreadsheet` → `/builds/export`; `Sell_Hesitation` → `docs/VAAS.md`),
so the manifest documents the system rather than diverging from it.

### `oceanic_os.py` boots the live stack from the manifest
The CLI parses the manifest and then **instantiates** the components each layer
maps to, reporting their real status — the threshold in force, the dissent
panel's actual size, the checkpoint policy, the anchor's presence, the manifest
hash — not an echo of the declared values. `--state stateless` boots against an
ephemeral database so it touches no durable state. It always exits 0: the system
continues.

### The Anchor of Last Resort
`boot/anchor_2019.txt` is a real 2019 dataset — the Gregorian calendar of 2019,
every date and weekday — generated deterministically from the C stdlib, so it is
provably correct and needs no network. It carries the sha256 of its own body.
`anchor.py` reads it, recomputes the hash to confirm integrity, and answers
lookups (`anchor_line("2019-07-04")`) with nothing else running. `GET /anchor`
surfaces it live.

## Consequences

- The invocation is now literal: `python oceanic_os.py --boot boot/init.v1
  --state stateless --exit 0` exits 0 and prints the booted stack, layer by
  layer, with the manifest hash and `anchor: present`.
- Degradation has a floor. Past the CSV export, past the spreadsheet, the anchor
  is a single stale `.txt` that answers offline — verified live: a build for the
  weekday of any 2019 date is returned by `anchor.anchor_line` with no service,
  database, or model in the loop. The last thing still true is time itself.
- Why the calendar and not a fetched dataset: it must be correct without a
  network and must not drift. A stdlib-generated 2019 calendar is verifiable
  against `calendar.weekday` and cannot rot; a downloaded dataset could be wrong,
  unavailable, or unredistributable. The anchor's value is that it never fails.
- The frontend's deliberate render latency was aligned to the manifest's
  `2500ms` (from 4000ms) so the ratified artifact and the running UI agree.
