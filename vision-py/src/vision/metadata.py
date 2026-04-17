from __future__ import annotations

DEFAULT_FORM = "unknown"
DEFAULT_MEGA_STATE = "base"
ALLOWED_MEGA_STATES = ("base", "mega")


def normalize_mega_state(value: str) -> str:
    normalized = value.strip().lower()
    if not normalized:
        return DEFAULT_MEGA_STATE
    if normalized not in ALLOWED_MEGA_STATES:
        allowed_values = ", ".join(ALLOWED_MEGA_STATES)
        raise ValueError(
            f"mega_state must be one of: {allowed_values}; got {value!r}"
        )
    return normalized
