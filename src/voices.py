from dataclasses import dataclass


@dataclass(frozen=True)
class Voice:
    name: str
    id: str


VOICES: list[Voice] = [
    Voice(name="Голос 4 (Frederick Surrey)", id="5b7b975cbbfe431f894d06dff2fe6792"),
    Voice(name="Голос 1 (Brian)", id="46e25ec695044696ac5f01788e0392bf"),
    Voice(name="Голос 5 (Arthur)", id="771a9dbd69704fdd952b6bf0d01db45b"),
    Voice(name="Голос 6 (James)", id="21a47a6e586842ac90b53f4e4360b997"),
    Voice(name="Голос 7", id="79b534a1718e4088a136706594cc1da0"),
]
