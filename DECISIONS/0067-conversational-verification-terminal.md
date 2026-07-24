# 0067 — Conversational Verification Terminal (the OS face)

## Context

The platform's face was the operator console — a dense grid of panels for driving
the system directly. Powerful, but it presumes an operator. The one interaction
model everyone now understands is chat, and the Doctrine's Interface layer calls
for a *verification terminal*, not a friendly chatbot. The opportunity: make the
OS face a conversational surface that does not betray the creed — you send a
claim, and it does not *answer* it, it *attests* it.

## Decision

Serve a ChatGPT-style verification chat at `/`, and move the full operator console
to `/console`.

- `templates/chat.html` is a self-contained conversational terminal: a message
  thread, a composer (Enter to send), and — for each message — a POST to
  `/builder/run` that convenes the panel and returns an attestation. The response
  bubble shows the verdict (**attested** / **held**), a confidence meter, the
  panel's dissent as per-adapter dots with the majority, the content hash, and the
  source count. The `2500 ms` render friction is preserved as a "convening the
  panel — validated hesitation" state.
- The aesthetic is "max mood": a layered cosmic background (nebula gradients, a
  drifting aurora, a faint starfield), a gradient `Ω∞v` sigil, glassmorphic
  cards, and a glowing composer — the beauty of the universe compressed into the
  OS UI, committed to a single deliberate dark look.
- `/` now renders the chat; `/console` renders the operator console unchanged, and
  the chat links to it.

## Consequences

- The creed is enacted in the interaction itself: verified live in a browser,
  sending "Build the charter ratification workflow" returns **ATTESTED at 0.90**
  with the panel dissenting (majority approve) and a real content hash, and a
  second prompt returns **0.80 / majority revise** — the terminal *attests*, it
  never *answers*. A held result (below `0.74`) renders the amber **held** verdict
  routed for review, so the friction and the threshold are visible, not hidden.
- Nothing was lost: the operator console is intact at `/console`, every panel and
  test preserved; only its address changed. The chat is a thin client over the
  existing `/builder/run` pipeline — no new server logic, no new state.
- The self-check still holds: the Doctrine's Interface layer cites `/`, which
  still resolves, now as the conversational terminal it always described. The two
  faces — chat for anyone, console for the operator — are the same platform.
- This is presentation with intent: a chatbot would generate an answer and hide
  its uncertainty; this terminal shows the confidence, the dissent, and the hash
  on every turn, so the interface teaches the thesis — certainty is a bug,
  verification is the product — the moment someone types.
