from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from vision.transport.client import (
    OverlayRequestError,
    post_observation,
    write_overlay_response_json,
)


class FakeHTTPResponse:
    def __init__(self, payload: object) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload, ensure_ascii=False).encode("utf-8")

    def __enter__(self) -> "FakeHTTPResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class OverlayTransportTest(unittest.TestCase):
    @mock.patch("vision.transport.client.request.urlopen")
    def test_post_observation_returns_overlay_payload(self, mock_urlopen: mock.Mock) -> None:
        mock_urlopen.return_value = FakeHTTPResponse(
            {
                "player": {"display_name": "サーフゴー", "speed_actual": 149},
                "opponent": {
                    "display_name": "ガブリアス",
                    "speed_candidates": {
                        "fastest": 169,
                        "neutral": 154,
                        "scarf_fastest": 253,
                        "scarf_neutral": 231,
                    },
                },
                "judgement": {
                    "vs_fastest": "lose",
                    "vs_neutral": "lose",
                    "vs_scarf_fastest": "lose",
                    "vs_scarf_neutral": "lose",
                },
            }
        )

        observation_payload = {
            "scene": "battle",
            "player_active": {"species_id": "greninja", "mega_state": "mega"},
            "opponent_active": {"species_id": "garchomp", "mega_state": "base"},
        }

        payload = post_observation(observation_payload)

        self.assertEqual(payload["player"]["speed_actual"], 149)
        self.assertEqual(payload["opponent"]["display_name"], "ガブリアス")
        request_payload = json.loads(mock_urlopen.call_args.args[0].data.decode("utf-8"))
        self.assertEqual(request_payload["player_active"]["mega_state"], "mega")
        self.assertEqual(request_payload["opponent_active"]["mega_state"], "base")

    @mock.patch("vision.transport.client.request.urlopen", side_effect=TimeoutError())
    def test_post_observation_raises_clear_error_on_timeout(self, mock_urlopen: mock.Mock) -> None:
        with self.assertRaises(OverlayRequestError):
            post_observation({"scene": "battle"})

    def test_write_overlay_response_json_writes_pretty_json(self) -> None:
        payload = {
            "player": {"display_name": "unknown", "speed_actual": 0},
            "opponent": {
                "display_name": "unknown",
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

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "overlay_response.json"
            write_overlay_response_json(payload, output_path)

            self.assertTrue(output_path.exists())
            loaded = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["player"]["speed_actual"], 0)
