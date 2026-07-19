# Layer 0: Reality

The ground truth layer — what the system can actually observe and prove.

## Working implementations

| Concept | Module | Notes |
| --- | --- | --- |
| Liveness | `server.py` `health()` | The service reports its own observable state, including its charter identity |
| Event ground truth | `state.py` | Every significant event is recorded in the state snapshot |
| Agent observability | `agent.py` | Agent runs emit an inspectable event stream |
| Content ground truth | `attestation.py` | Build records are hashed (SHA-256); the hash is the reality check |
| External ground truth | `tool_plugins.py` `GitHubTools` | Successful API responses are cached in the `ground_truth` SQLite table; when the network fails, the system degrades to its own last-verified copy, marked stale |

## Principles applied

- Reality before assumption: nothing is reported that was not observed.
- Evidence before conclusion: confidence scores count evidence; they never claim certainty.
