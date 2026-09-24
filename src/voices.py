from dataclasses import dataclass


@dataclass(frozen=True)
class Voice:
    name: str
    id: str


VOICES: list[Voice] = [
    Voice(name="Голос 4 (Frederick Surrey)", id="5b7b975cbbfe431f894d06dff2fe6792"),
    Voice(name="Голос 1 (Brian)", id="46e25ec695044696ac5f01788e0392bf"),
    Voice(name="Голос 5 (Narrator)", id="3f6222cbc94d40a087cdb94ee14fdb0f"),
    Voice(name="Голос 6 (James)", id="21a47a6e586842ac90b53f4e4360b997"),
    Voice(name="Голос 7", id="79b534a1718e4088a136706594cc1da0"),
    Voice(name="Голос 8 (Laura)", id="e3cd384158934cc9a01029cd7d278634"),
    Voice(name="Голос 9 (Dec1)", id="991d730f2f4a42a7b50467cf502350ec"),
    Voice(name="Голос 10", id="211282d53ffb4f4f852b9915ea39bd9a"),
    Voice(name="Голос 11 (Сергей Бурунов)", id="4fc46239da68494c9caf50466b28e320"),
    Voice(name="Голос 12 (Елена Шульман)", id="d0b4f3fe65314a649011a375761e6370"),
    Voice(name="Голос 13", id="8336207c3431432cb60e8851e78ba437"),
    Voice(name="Голос 14", id="aa615eaff73f417e91cfbb4ea0e42df8"),
    Voice(name="Голос 15 (Rome 1 ESP)", id="dfa5b230c8054f429e434f4a6e9bbdec"),
    Voice(name="Голос 16 (Rome 1 POR)", id="04736e4d6a644abab81e601a7d2ae4b9"),
    Voice(name="Голос 17 (Rome 1 GER)", id="90042f762dbf49baa2e7776d011eee6b"),
    Voice(name="Голос 18 (FR)", id="9f0935a47689459480b820ed3f6d782d"),
    Voice(name="Голос 19 (PL)", id="2532d01f4c59446d9e2144803b73e9da"),
    Voice(name="Голос 20 (ITA)", id="14e71c0c9fb54062b0fd713aed6cf5a0"),
]
