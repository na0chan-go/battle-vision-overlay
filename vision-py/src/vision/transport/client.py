from __future__ import annotations

import json
from pathlib import Path
from urllib import error, request


DEFAULT_OVERLAY_ENDPOINT = "http://localhost:8080/api/v1/overlay/preview"


class OverlayRequestError(RuntimeError):
    """Raised when the overlay preview request fails."""


def build_overlay_error_response(message: str, detail: str = "unknown") -> dict[str, object]:
    return {
        "status": "error",
        "message": message,
        "error": {
            "message": message,
            "detail": detail,
        },
        "player": {
            "display_name": "unknown",
            "gender": "unknown",
            "form": "unknown",
            "mega_state": "unknown",
            "speed_actual": 0,
        },
        "opponent": {
            "display_name": "unknown",
            "gender": "unknown",
            "form": "unknown",
            "mega_state": "unknown",
            "speed_candidates": {
                "fastest": 0,
                "neutral": 0,
                "scarf_fastest": 0,
                "scarf_neutral": 0,
            },
        },
        "judgement": {
            "vs_fastest": "unknown",
            "vs_neutral": "unknown",
            "vs_scarf_fastest": "unknown",
            "vs_scarf_neutral": "unknown",
        },
    }


def post_observation(
    observation_payload: dict[str, object],
    *,
    endpoint_url: str = DEFAULT_OVERLAY_ENDPOINT,
    timeout: float = 5.0,
) -> dict[str, object]:
    body = json.dumps(observation_payload, ensure_ascii=False).encode("utf-8")
    http_request = request.Request(
        endpoint_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(http_request, timeout=timeout) as response:
            raw_body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        raise OverlayRequestError(
            f"overlay request failed with status {exc.code}"
        ) from exc
    except error.URLError as exc:
        raise OverlayRequestError(
            f"overlay request failed: {exc.reason}"
        ) from exc
    except TimeoutError as exc:
        raise OverlayRequestError("overlay request timed out") from exc

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise OverlayRequestError("overlay response was not valid JSON") from exc

    if not isinstance(payload, dict):
        raise OverlayRequestError("overlay response must be a JSON object")

    return payload


def write_overlay_response_json(payload: dict[str, object], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
