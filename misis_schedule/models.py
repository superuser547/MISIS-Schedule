"""Нормализованные модели расписания."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from enum import Enum


class WeekType(Enum):
    """Тип недели, к которому относится строка Excel-расписания."""

    UPPER = "upper"
    LOWER = "lower"

    @property
    def label(self) -> str:
        """Возвращает русское название типа недели для интерфейса."""

        return "Верхняя неделя" if self is WeekType.UPPER else "Нижняя неделя"


@dataclass(frozen=True)
class Lesson:
    """Одно занятие без привязки к датам конкретного семестра."""

    subject: str
    location: str | None
    weekday: int
    pair_number: int
    start_time: time
    end_time: time
    week_type: WeekType
    group_name: str
    subgroup_number: int


@dataclass(frozen=True)
class GroupLayout:
    """Границы блока группы и колонки её реально существующих подгрупп."""

    group_name: str
    start_column: int
    end_column: int
    subgroup_columns: dict[int, tuple[int, int]]
