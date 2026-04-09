from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ActivePokemonObservation:
    species_id: str
    display_name: str
    gender: str
    form: str
    mega_state: str
    confidence: float

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["confidence"] = round(float(self.confidence), 4)
        return payload


@dataclass(frozen=True)
class Observation:
    scene: str
    timestamp: int
    player_active: ActivePokemonObservation
    opponent_active: ActivePokemonObservation

    def to_dict(self) -> dict[str, object]:
        return {
            "scene": self.scene,
            "timestamp": self.timestamp,
            "player_active": self.player_active.to_dict(),
            "opponent_active": self.opponent_active.to_dict(),
        }
