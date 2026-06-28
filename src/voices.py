from dataclasses import dataclass


@dataclass(frozen=True)
class Voice:
    name: str
    id: str


VOICES: list[Voice] = [
    Voice(name="Голос 1", id="5b7b975cbbfe431f894d06dff2fe6792"),
    Voice(name="Голос 4", id="46e25ec695044696ac5f01788e0392bf"),
]
