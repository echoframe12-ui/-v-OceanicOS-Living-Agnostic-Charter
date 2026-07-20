from __future__ import annotations

import os
from typing import Any

# VaaS tiers (see docs/VAAS.md) mapped to build quotas per rolling window.
# None = unlimited. Higher pay, higher ceiling — the premium buys the
# humanosecond at scale.
TIER_LIMITS: dict[str, int | None] = {
    "attestor": 10,
    "arbiter": 50,
    "sovereign": None,
}
DEFAULT_TIER = "attestor"

# The quota window: tier limits are builds per this many seconds, resetting
# continuously as older builds age out. Default one hour.
WINDOW_SECONDS = int(os.getenv("OCEANICOS_QUOTA_WINDOW", "3600"))


def is_tier(tier: str) -> bool:
    return tier in TIER_LIMITS


def limit_for(tier: str) -> int | None:
    """The build ceiling for a tier; unknown tiers fall back to the default."""
    return TIER_LIMITS.get(tier, TIER_LIMITS[DEFAULT_TIER])


def quota_status(
    tier: str,
    used: int,
    window_seconds: int | None = None,
    resets_at: str | None = None,
) -> dict[str, Any]:
    """Report a tier's build quota against usage in the current window.

    An unlimited tier (limit None) is never exceeded and has no remaining
    ceiling. A finite tier is exceeded once in-window usage reaches the limit.
    `window_seconds` and `resets_at` describe the rolling window when supplied.
    """
    limit = limit_for(tier)
    remaining = None if limit is None else max(0, limit - used)
    exceeded = limit is not None and used >= limit
    return {
        "tier": tier,
        "limit": limit,
        "used": used,
        "remaining": remaining,
        "exceeded": exceeded,
        "window_seconds": window_seconds,
        "resets_at": resets_at,
    }
