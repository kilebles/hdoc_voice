from dataclasses import dataclass


@dataclass(frozen=True)
class Voice:
    name: str
    id: str


VOICES: list[Voice] = [
    Voice(name="Brian Deep Resonant", id="46e25ec695044696ac5f01788e0392bf"),
    Voice(name="Brian - deep, resonant", id="3ab0b30ff9fc4e6da74cbd91bbc579c1"),
    Voice(name="Frederick Surrey", id="5b7b975cbbfe431f894d06dff2fe6792"),
]
