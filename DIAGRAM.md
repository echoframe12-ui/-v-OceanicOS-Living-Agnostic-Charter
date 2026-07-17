# Architecture Diagram

```text
User / Contributor
        |
        v
Interface Layer
        |
        v
Planning Layer --> Memory Layer
        |                |
        v                v
Tool Layer      Model Layer
        \              /
         \            /
          v          v
       API / Plugin Layer
```

## Flow Summary

1. A user or contributor submits a request.
2. The planning layer creates a structured plan.
3. Memory and tools provide context and actions.
4. The model layer contributes reasoning and generation.
5. The API and plugin layer expose the orchestration behavior to the wider ecosystem.
