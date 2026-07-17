# OceanicOS Living Agnostic Charter

This repository is the starting point for a living, agnostic charter for OceanicOS: a flexible framework for building open, resilient, and human-centered systems without locking the project into rigid assumptions.

## Status: Activated

The repository is now initialized with a constitutional framework, a practical platform foundation, and a runnable prototype for an open orchestration layer.

## Purpose

The purpose of this charter is to define the values, principles, and working habits that guide the project over time. It should remain adaptable, clear, and useful as the project evolves.

## Core Principles

Every implementation and task execution within this framework should uphold:

1. Reality before assumption.
2. Evidence before conclusion.
3. Truth before convenience.
4. Humans remain accountable.
5. Respect dignity, privacy, and consent.
6. Explain significant reasoning where appropriate.
7. Preserve provenance and history.
8. Design for interoperability.
9. Learn continuously.
10. Steward for future generations.

The practical project principles are also expressed as:

- Openness: make decisions, processes, and knowledge understandable and shareable.
- Interoperability: favor systems and practices that work well across contexts and communities.
- Human agency: keep people, dignity, and consent at the center of design and governance.
- Resilience: build for continuity, recovery, and long-term sustainability.
- Inclusivity: welcome diverse perspectives and reduce unnecessary barriers to participation.

## Constitution and Platform Foundations

OceanicOS is not intended to become a single chatbot. It is intended to become an open orchestration layer that can:

- preserve memory across work and sessions
- plan and explain its reasoning
- coordinate tools such as GitHub, calendars, files, and external services
- work with multiple models and providers
- remain transparent, auditable, and adaptable

The foundational documents are:

- [CONSTITUTION.md](CONSTITUTION.md) for the operating principles and governance rules
- [ARCHITECTURE.md](ARCHITECTURE.md) for the system layers and execution model
- [MEMORY.md](MEMORY.md) for the persistent memory approach
- [GOVERNANCE.md](GOVERNANCE.md) for the stewardship and review model
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for the first practical build phases
- [API_SPEC.md](API_SPEC.md) for the initial orchestration API and plugin model
- [DIAGRAM.md](DIAGRAM.md) for the architecture overview
- [OPEN_ORCHESTRATION_SPEC.md](OPEN_ORCHESTRATION_SPEC.md) for the consolidated platform specification
- [ROADMAP.md](ROADMAP.md) for the implementation milestones

## Platform Direction

OceanicOS is now structured as an open orchestration layer with a foundation for:

- planning and reasoning
- persistent memory
- workflow execution
- tool integration
- model routing
- observable agent events

The consolidated spec is available in [OPEN_ORCHESTRATION_SPEC.md](OPEN_ORCHESTRATION_SPEC.md).

## Starter Implementation

A minimal starter service is now included in [server.py](server.py), with a Flask-based HTTP interface in [app.py](app.py), a runnable demo in [main.py](main.py), and a browser-based builder entry point in [templates/index.html](templates/index.html). It demonstrates:

- a health endpoint
- plan creation
- persistent memory storage and lookup via SQLite
- a small tool registry with an echo tool
- a simple plugin registration model for future integrations
- a workflow engine for creating and executing multi-step plans
- an interactive builder experience that runs planning, routing, review, and artifact creation

Run the demo with:

```bash
python main.py
```

Run the Flask app with:

```bash
python app.py
```

Then open the starter UI at http://127.0.0.1:5000/.

Use the endpoints:

- GET /health
- POST /plans
- POST /memory
- GET /memory?query=review
- GET /tools
- POST /tools/echo
- POST /workflows
- GET /workflows/<name>
- POST /workflows/<name>/execute
- POST /plans/execute
- GET /plans/trace
- POST /models/route
- POST /agent/run
- GET /agent/events
- POST /state
- GET /state
- POST /reviews
- POST /reviews/<proposal>/approve
- GET /reviews
- POST /decisions
- GET /decisions
- POST /artifacts
- GET /artifacts
- POST /dashboard
- GET /dashboard
- POST /plugins
- GET /plugins
- POST /builder/run
- GET /builder/history
- POST /builder/evolve

Run the universal builder with:

```bash
python universal_builder.py
```

Run the test suite with:

```bash
python -m pytest -q
```

You can also configure host, port, and debug settings with environment variables:

```bash
HOST=127.0.0.1 PORT=9000 FLASK_DEBUG=0 python app.py
```

> Reality is the source. Evidence guides understanding. Humans lead. OceanicOS connects. Better reality is the outcome.

## Deployment

The app ships as a full-stack deployable service:

- [wsgi.py](wsgi.py) exposes the Flask app for any WSGI server
- [Procfile](Procfile) runs the app under gunicorn for Heroku-style platforms
- [Dockerfile](Dockerfile) builds a self-contained container image

Run in production mode locally:

```bash
pip install -r requirements.txt
gunicorn --bind 0.0.0.0:5000 wsgi:app
```

Or with Docker:

```bash
docker build -t oceanicos .
docker run -p 5000:5000 oceanicos
```

The SQLite database location can be configured with the `OCEANICOS_DB` environment variable (defaults to `oceanicos.db` in the working directory).

## Scope

This charter is intended to guide:

- project governance and collaboration
- architectural and technical direction
- ethical and social considerations
- long-term stewardship of the initiative

It is not meant to be a rigid rulebook. Instead, it should evolve as the project learns and grows.

## First Commitments

- Keep the charter simple and legible.
- Prefer reversible and transparent choices.
- Document decisions in a way that future contributors can understand.
- Treat the charter as a living document, not a final verdict.

## How to Contribute

Contributions can be made by proposing edits, refining principles, or suggesting new sections that improve clarity and usefulness. The best contributions are grounded in the project’s values and written in a way that helps others participate.

## Becoming

OceanicOS is a process, not a fixed destination. To continue becoming means:

- practicing iteration over perfection
- keeping the charter visible and easy to update
- testing ideas with small, real experiments
- learning from what works and what doesn’t
- making space for new contributors to shape the project

This repository is the first seed of that process. The next stage is to turn this charter into accessible practices and shared outcomes.

## Vision

OceanicOS is meant to be a living, agnostic approach to building systems that are adaptable, collaborative, and human-centered. The charter should help maintain momentum while avoiding rigid, gatekeeping structures.

## Next Steps

- Clarify the project’s target audience and use cases.
- Define the first practical goals or deliverables for OceanicOS.
- Add a short roadmap or milestones section.
- Establish a lightweight process for decision-making and updates.
- Invite collaborators to review and refine the charter.
- Implement the first working orchestration loop around planning, memory, and tool use.

## Related resources

- See [ROADMAP.md](ROADMAP.md) for the initial milestones and goals.
- See [CONSTITUTION.md](CONSTITUTION.md) for the rules that guide the project.
