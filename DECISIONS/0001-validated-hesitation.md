# Decision 0001: Adopt the Validated Hesitation (Friction) Protocol

## Context

OceanicOS races nowhere. In a landscape optimizing for zero latency and
frictionless generation, the charter's principles — evidence before
conclusion, humans remain accountable, preserve provenance — imply the
opposite posture: outputs should be attested, not asserted, and hesitation
should be a designed feature, not an accident.

## Decision

The platform adopts the Full-Stack Vibe Protocol as working architecture:

1. **Attestation over generation.** Every builder run produces an
   attestation: a SHA-256 hash of the build record, a deterministic
   confidence score, the threshold it was judged against (0.74), and the
   full source trail of pipeline stages that produced it.
2. **Validated hesitation.** Builds whose confidence falls below the
   threshold are *held*: their review is never auto-approved, and the
   evolution report demands a human squint. Missing context is treated as
   missing evidence.
3. **Dissent as primary output.** The model router can run every matching
   adapter in parallel (`/models/consensus`); when results differ, dissent
   is the headline, not a footnote.
4. **Deliberate interface friction.** The browser UI is a monochrome
   verification terminal with a 2.5-second render delay — the
   computational cost made visible. It reports hashes, confidence, and
   source trails, never a single "final" answer.
5. **Graceful degradation into a spreadsheet.** The persistent build
   ledger exports as CSV (`/builds/export`); the system's ground truth
   survives without the system.

## Consequences

- Nothing auto-approves without evidence; low-evidence runs accumulate as
  held attestations until a human resolves them.
- The confidence score is honest about being an evidence count, not
  semantic certainty — certainty is a bug.
- The UI is slower by design; the delay is the product.
