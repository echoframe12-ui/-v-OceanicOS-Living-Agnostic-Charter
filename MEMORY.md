# Persistent Memory Model

Persistent memory is a core requirement for any serious orchestration system. It allows the platform to retain context, learn from experience, and explain its reasoning over time.

## Memory Types

- Working memory: short-lived context for the current task.
- Episodic memory: records of prior actions, outcomes, and lessons.
- Semantic memory: durable facts, principles, and shared knowledge.
- Shared memory: repository notes, decision records, and documented agreements.

## Memory Rules

- Every memory entry should carry a source, timestamp, and confidence level.
- Sensitive data should be handled carefully and stored with clear access boundaries.
- Memory should support both human review and machine retrieval.
- The system should distinguish between facts, assumptions, and unresolved questions.

## Memory Workflow

1. Capture relevant context.
2. Normalize it into durable records.
3. Link it to decisions, tasks, or documents.
4. Retrieve it when similar work recurs.
5. Review and refine it over time.
