# 0004 — Admin / Stewardship Role

## Context

Round 9 scoped each member to their own slice — good for consent, but it left
no one able to see the whole. A living platform still needs stewardship:
someone accountable for the health of the commons (held attestations across
all actors, platform-wide verification trust, who is doing what). Scoping
without stewardship is fragmentation.

## Decision

Introduce a two-role model on identity:

- Every user has a `role` — `member` (default) or `admin`.
- Admins are named out-of-band via `OCEANICOS_ADMIN_USERS` (comma-separated)
  or the `AuthRegistry(admin_users=[...])` constructor. Membership in that set
  at registration time assigns the admin role. Admins are *appointed*, never
  self-selected — a user cannot promote themselves.
- A `require_admin` gate returns **403** to non-admins. It guards the
  stewardship surface: `GET /admin/overview` (platform totals: users, builds,
  attestations, held count, global CVI, the set of actors) and
  `GET /admin/users` (usernames, roles, and per-actor build counts).

Members keep their scoped `/me/*` views unchanged. The admin views are
**aggregate and governance-oriented** — counts, roles, held work — not a
back door into the content of another member's private slice.

## Consequences

- Stewardship (Layer 9) becomes concrete: an accountable role can watch the
  health of the whole without dissolving members' scoping.
- The framing matters — this is transparency for governance, not
  surveillance. The admin surface is deliberately aggregate.
- Appointment is external (env/config), so the role can't be seized from
  inside the running system.
