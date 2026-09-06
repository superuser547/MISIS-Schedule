"""Правила отображения аудиторий МИСИС."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class LocationInfo:
    """Аудитория для календаря и дополнительные строки её описания."""

    display_location: str | None
    description_lines: tuple[str, ...] = ()


def enrich_location(location: str | None) -> LocationInfo:
    """Дополняет аудиторию информацией о корпусах Б и Г."""

    if location is None or not location.strip():
        return LocationInfo(display_location=None)

    normalized = location.strip()
    g_room_match = re.fullmatch(r"Г-?(\d+)", normalized)
    if g_room_match:
        room_number = g_room_match.group(1)
        floor = int(room_number[0])
        room = int(room_number[1:]) if len(room_number) > 1 else None
        pink_room_ranges = {3: (34, 82), 4: (57, 108), 5: (59, 104)}
        room_range = pink_room_ranges.get(floor)
        if room_range and room is not None and room_range[0] <= room <= room_range[1]:
            return LocationInfo(
                display_location=f"{normalized} (розовый корпус)",
                description_lines=("Аудитория расположена в «розовом» корпусе Г.",),
            )

    if not normalized.startswith("Б-"):
        return LocationInfo(display_location=normalized)

    room_part = normalized.split("-", maxsplit=1)[1].strip()
    if len(room_part) == 1 and room_part.isdigit():
        return LocationInfo(
            display_location=f"{normalized} (1-й этаж)",
            description_lines=("Аудитория расположена на первом этаже.",),
        )

    match = re.match(r"^(10|11|[1-9])", room_part)
    if not match:
        # Нестандартную запись нельзя надёжно расшифровать, но она всё ещё
        # пригодна как LOCATION и не должна мешать созданию календаря.
        return LocationInfo(display_location=normalized)

    floor = int(match.group(1))
    if floor in {2, 6, 9, 10}:
        elevator_note = "Можно использовать любой из лифтов в корпусе Б."
        elevator_label = "Любые лифты"
    else:
        elevator_note = "Можно использовать только левые лифты в корпусе Б."
        elevator_label = "Только левые лифты"

    return LocationInfo(
        display_location=f"{normalized} ({elevator_label})",
        description_lines=(elevator_note,),
    )
