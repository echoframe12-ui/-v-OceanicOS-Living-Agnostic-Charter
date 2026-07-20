# 0016 — One Canonical Identity Lineage

## Context

By round 21 the stack could boot itself and report its layers, and `/observer`
reported root, sigil, and the manifest hash — but nothing stated the system's
*identity*: what it is, root to charter. The Observer sent that lineage as a bare
tree (`/ → Ω∞v Compiler → OceanicOS → Living Agnostic Charter`). Left as prose it
would drift; restated in the banner, the endpoint, and the README separately it
would diverge. A system that verifies things for a living should not say three
slightly different names of itself.

## Decision

Make the lineage one shared artifact.

- `identity.py` holds the canonical `TREE` (name + gloss, root-first),
  `as_list()`, and `render()` (the exact nested tree). It is the single source.
- The boot report (`oceanic_os.py`) and `/observer` both import it — `identity`
  in the report/payload, `render()` in the boot banner — so they state the same
  name from the same place.
- `TREE.md` is the human front door to that same structure.

## Consequences

- The system says one name of itself everywhere: the boot banner, the root
  endpoint, and the repo all resolve to `identity.py`. Change the lineage once
  and every surface follows; there is no second copy to fall out of sync.
- It is inert and offline: `identity.render()` prints the tree with nothing
  running, like the Anchor — identity is not a service, it is a fact.
- Deliberately small. This adds a name, not behavior; no endpoint contract or
  ledger guarantee changes. It is the capstone of the boot arc (rounds 21–22):
  the stack can instantiate itself, and now it can say what it is.
