"""Разбор актуального формата Excel-расписаний МИСИС."""

from __future__ import annotations

import re
from datetime import time
from os import PathLike
from typing import Any, BinaryIO

import pandas as pd

from .exceptions import ScheduleParseError
from .models import GroupLayout, Lesson, WeekType

ExcelSource = str | PathLike[str] | BinaryIO

DAY_NAMES = {
    "понедельник": 0,
    "вторник": 1,
    "среда": 2,
    "четверг": 3,
    "пятница": 4,
    "суббота": 5,
    "воскресенье": 6,
}
TIME_RANGE_RE = re.compile(
    r"^\s*(?P<start>\d{1,2}:\d{2}(?::\d{2})?)\s*[-–—]\s*"
    r"(?P<end>\d{1,2}:\d{2}(?::\d{2})?)\s*$"
)


def get_sheet_names(source: ExcelSource) -> list[str]:
    """Возвращает реальные имена листов загруженного Excel-файла."""

    try:
        with pd.ExcelFile(source) as workbook:
            sheet_names = workbook.sheet_names
    except Exception as exc:  # pandas объединяет ошибки движков Excel
        raise ScheduleParseError(
            "Не удалось открыть Excel-файл. Проверьте, что загружен корректный .xls или .xlsx."
        ) from exc

    if not sheet_names:
        raise ScheduleParseError("В Excel-файле не найдено ни одного листа.")
    return sheet_names


def read_sheet(source: ExcelSource, sheet_name: str) -> pd.DataFrame:
    """Читает лист без преобразования строк заголовков в имена колонок."""

    try:
        frame = pd.read_excel(source, sheet_name=sheet_name, header=None)
    except ValueError as exc:
        raise ScheduleParseError(f"Лист «{sheet_name}» не найден в Excel-файле.") from exc
    except Exception as exc:
        raise ScheduleParseError(f"Не удалось прочитать лист «{sheet_name}».") from exc

    if frame.shape[0] < 3 or frame.shape[1] < 5:
        raise ScheduleParseError(
            "Не удалось распознать заголовок: ожидаются две строки заголовка и блоки групп."
        )
    return frame


def get_groups(sheet: pd.DataFrame) -> list[str]:
    """Возвращает список академических групп на выбранном листе."""

    _validate_service_columns(sheet)
    groups: list[str] = []
    for value in sheet.iloc[0, 3:].tolist():
        name = _clean_string(value)
        if name and name not in groups:
            groups.append(name)
    if not groups:
        raise ScheduleParseError("На выбранном листе не найдены академические группы.")
    return groups


def available_subgroups(sheet: pd.DataFrame, group_name: str) -> list[int]:
    """Возвращает номера подгрупп, существующие внутри блока выбранной группы."""

    return sorted(get_group_layout(sheet, group_name).subgroup_columns)


def get_group_layout(sheet: pd.DataFrame, group_name: str) -> GroupLayout:
    """Определяет точные границы блока группы и пары колонок её подгрупп."""

    groups = _group_positions(sheet)
    if group_name not in groups:
        raise ScheduleParseError(f"Группа «{group_name}» не найдена на выбранном листе.")

    start = groups[group_name]
    starts = sorted(groups.values())
    next_start = next((column for column in starts if column > start), sheet.shape[1])
    width = next_start - start
    if width < 2 or width % 2:
        raise ScheduleParseError(f"У группы «{group_name}» неожиданная структура блока колонок.")

    pair_count = width // 2
    labels = [
        _parse_subgroup_number(sheet.iat[1, start + index * 2]) for index in range(pair_count)
    ]
    if all(label is None for label in labels):
        # В некоторых листах магистратуры номера подгрупп не записаны. Тогда
        # каждая физическая пара «предмет + аудитория» остаётся отдельной подгруппой.
        labels = list(range(1, pair_count + 1))
    elif any(label is None for label in labels) or len(set(labels)) != len(labels):
        raise ScheduleParseError(
            f"Не удалось однозначно распознать подгруппы группы «{group_name}»."
        )

    subgroup_columns = {
        int(label): (start + index * 2, start + index * 2 + 1) for index, label in enumerate(labels)
    }
    return GroupLayout(group_name, start, next_start, subgroup_columns)


def parse_schedule(sheet: pd.DataFrame, group_name: str, subgroup_number: int) -> list[Lesson]:
    """Разбирает выбранную группу и подгруппу в нормализованный список занятий."""

    layout = get_group_layout(sheet, group_name)
    columns = layout.subgroup_columns.get(subgroup_number)
    if columns is None:
        available = ", ".join(map(str, sorted(layout.subgroup_columns)))
        raise ScheduleParseError(
            f"У группы «{group_name}» нет подгруппы {subgroup_number}. Доступны: {available}."
        )
    subject_column, location_column = columns

    lessons: list[Lesson] = []
    current_day: int | None = None
    row_index = 2
    while row_index < len(sheet):
        day_value = _clean_string(sheet.iat[row_index, 0])
        if day_value:
            current_day = _parse_weekday(day_value, row_index)

        pair_value = sheet.iat[row_index, 1]
        if _is_empty(pair_value):
            row_index += 1
            continue
        if current_day is None:
            raise ScheduleParseError(
                f"Не удалось определить день недели для строки расписания {row_index + 1}."
            )

        pair_number = _parse_pair_number(pair_value, row_index)
        start_time, end_time = _parse_time_range(sheet.iat[row_index, 2], pair_number, row_index)
        rows = ((WeekType.UPPER, row_index), (WeekType.LOWER, row_index + 1))
        for week_type, lesson_row in rows:
            if lesson_row >= len(sheet):
                break
            subject = _clean_string(sheet.iat[lesson_row, subject_column])
            if subject is None:
                continue
            lessons.append(
                Lesson(
                    subject=subject,
                    location=_clean_string(sheet.iat[lesson_row, location_column]),
                    weekday=current_day,
                    pair_number=pair_number,
                    start_time=start_time,
                    end_time=end_time,
                    week_type=week_type,
                    group_name=group_name,
                    subgroup_number=subgroup_number,
                )
            )
        # По формату МИСИС следующая строка той же пары — нижняя неделя.
        row_index += 2
    return lessons


def _validate_service_columns(sheet: pd.DataFrame) -> None:
    expected = ("Дата", "Номер", "Время")
    actual = tuple(_clean_string(sheet.iat[0, index]) for index in range(3))
    if actual != expected:
        raise ScheduleParseError("Не удалось распознать служебные столбцы «Дата | Номер | Время».")


def _group_positions(sheet: pd.DataFrame) -> dict[str, int]:
    _validate_service_columns(sheet)
    positions: dict[str, int] = {}
    for column in range(3, sheet.shape[1]):
        name = _clean_string(sheet.iat[0, column])
        if name is None:
            continue
        if name in positions:
            raise ScheduleParseError(f"Группа «{name}» повторяется в заголовке листа.")
        positions[name] = column
    if not positions:
        raise ScheduleParseError("На выбранном листе не найдены академические группы.")
    return positions


def _parse_weekday(value: str, row_index: int) -> int:
    weekday = DAY_NAMES.get(value.strip().casefold())
    if weekday is None:
        raise ScheduleParseError(
            f"Не удалось распознать день недели «{value}» в строке {row_index + 1}."
        )
    return weekday


def _parse_pair_number(value: Any, row_index: int) -> int:
    try:
        number = int(float(value))
    except (TypeError, ValueError) as exc:
        raise ScheduleParseError(
            f"Не удалось определить номер пары в строке расписания {row_index + 1}."
        ) from exc
    if number < 1:
        raise ScheduleParseError(f"Некорректный номер пары {number} в строке {row_index + 1}.")
    return number


def _parse_time_range(value: Any, pair_number: int, row_index: int) -> tuple[time, time]:
    text = _clean_string(value)
    match = TIME_RANGE_RE.match(text or "")
    if match is None:
        raise ScheduleParseError(
            f"Не удалось определить время пары №{pair_number} в строке расписания {row_index + 1}."
        )
    try:
        start = time.fromisoformat(match.group("start"))
        end = time.fromisoformat(match.group("end"))
    except ValueError as exc:
        raise ScheduleParseError(
            f"Не удалось определить время пары №{pair_number} в строке расписания {row_index + 1}."
        ) from exc
    if end <= start:
        raise ScheduleParseError(
            f"Время окончания пары №{pair_number} должно быть позже времени начала."
        )
    return start, end


def _parse_subgroup_number(value: Any) -> int | None:
    if _is_empty(value):
        return None
    try:
        number = int(float(str(value).strip()))
    except (TypeError, ValueError) as exc:
        raise ScheduleParseError(f"Некорректный номер подгруппы «{value}».") from exc
    if number < 1:
        raise ScheduleParseError(f"Некорректный номер подгруппы «{value}».")
    return number


def _clean_string(value: Any) -> str | None:
    if _is_empty(value):
        return None
    return str(value).strip()


def _is_empty(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip()) or pd.isna(value)
