# Layer 4: Intelligence

This layer maps the intelligence concepts of the charter to their working
implementations in the codebase.

## Working implementations

| Concept | Module | Notes |
| --- | --- | --- |
| Planning and reasoning | `planner.py` | Produces structured plans with a persistent trace |
| Model routing | `models.py` | Keyword-based routing across registered adapters with a default fallback |
| Real dissent | `models.py` verdict strategies + `route_all` | Adapters reach genuine verdicts (`approve`/`revise`); the consensus panel reports the split, distribution, and majority — dissent is measured, not manufactured. See [DECISIONS/0007](../../DECISIONS/0007-real-dissent.md) |
| Real model provider | `claude_adapter.py` | Routes prompts to Claude through the official Anthropic SDK; enabled when `ANTHROPIC_API_KEY` is set |
| Agent loop | `agent.py` | Records observable agent events for each run |

## Principles applied

- Interoperability: adapters share one interface, so demo and real providers coexist.
- Reality before assumption: the Claude adapter registers only when real credentials exist; nothing pretends to be a model that is not there.
- Preserve provenance: every routed prompt returns which adapter and provider produced the result.
