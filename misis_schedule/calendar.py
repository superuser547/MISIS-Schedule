"""Создание календаря iCalendar из нормализованных занятий."""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from icalendar import Alarm, Calendar, Event, Timezone

from .exceptions import CalendarGenerationError
from .models import Lesson, WeekType
from .rules import enrich_location

MOSCOW_TZ = ZoneInfo("Europe/Moscow")
UID_NAMESPACE = uuid.UUID("6bbbd754-574f-5f23-a65a-8137d40b3b1d")


def validate_semester_dates(
    upper_week_start: date, lower_week_start: date, semester_end: date
) -> str | None:
    """Проверяет обязательные даты и возвращает предупреждение о чередовании недель."""

    if upper_week_start.weekday() != 0 or lower_week_start.weekday() != 0:
        raise CalendarGenerationError(
            "Начало верхней и нижней недели должно приходиться на понедельник."
        )
    if semester_end <= max(upper_week_start, lower_week_start):
        raise CalendarGenerationError(
            "Дата окончания семестра должна быть позже начала верхней и нижней недель."
        )
    if abs((lower_week_start - upper_week_start).days) != 7:
        return "Начало верхней и нижней недели обычно отличаются ровно на 7 дней."
    return None


def lesson_datetime(
    lesson: Lesson, upper_week_start: date, lower_week_start: date
) -> tuple[datetime, datetime]:
    """Преобразует логический слот занятия в timezone-aware начало и конец."""

    base_date = upper_week_start if lesson.week_type is WeekType.UPPER else lower_week_start
    event_date = date.fromordinal(base_date.toordinal() + lesson.weekday)
    start = datetime.combine(event_date, lesson.start_time, tzinfo=MOSCOW_TZ)
    end = datetime.combine(event_date, lesson.end_time, tzinfo=MOSCOW_TZ)
    return start, end


def build_calendar(
    lessons: Iterable[Lesson],
    upper_week_start: date,
    lower_week_start: date,
    semester_end: date,
) -> Calendar:
    """Создаёт календарь с занятиями раз в две недели до конца семестра."""

    validate_semester_dates(upper_week_start, lower_week_start, semester_end)
    calendar = Calendar()
    calendar.add("prodid", "-//MISIS Schedule//RU")
    calendar.add("version", "2.0")
    calendar.add("calscale", "GREGORIAN")
    calendar.add("method", "PUBLISH")
    calendar.add_component(Timezone.from_tzid("Europe/Moscow"))

    until = datetime.combine(semester_end, time.max, tzinfo=MOSCOW_TZ).astimezone(UTC)
    for lesson in lessons:
        if not lesson.subject.strip():
            continue
        start, end = lesson_datetime(lesson, upper_week_start, lower_week_start)
        if start.date() > semester_end:
            continue
        _add_event(calendar, lesson, start, end, until, upper_week_start, lower_week_start)
    return calendar


def stable_uid(lesson: Lesson, upper_week_start: date, lower_week_start: date) -> str:
    """Возвращает стабильный UID слота в конкретном семестре без текста занятия."""

    slot = "|".join(
        (
            lesson.group_name,
            str(lesson.subgroup_number),
            upper_week_start.isoformat(),
            lower_week_start.isoformat(),
            lesson.week_type.value,
            str(lesson.weekday),
            str(lesson.pair_number),
        )
    )
    return f"{uuid.uuid5(UID_NAMESPACE, slot)}@misis-schedule"


def _add_event(
    calendar: Calendar,
    lesson: Lesson,
    start: datetime,
    end: datetime,
    until: datetime,
    upper_week_start: date,
    lower_week_start: date,
) -> None:
    event = Event()
    location = enrich_location(lesson.location)
    description_lines = [lesson.subject]
    if location.display_location:
        description_lines.append(location.display_location)
    description_lines.append(lesson.week_type.label)
    description_lines.extend(location.description_lines)

    event.add("uid", stable_uid(lesson, upper_week_start, lower_week_start))
    event.add("dtstamp", datetime.now(UTC))
    event.add("dtstart", start)
    event.add("dtend", end)
    event.add("summary", lesson.subject)
    event.add("description", "\n".join(description_lines))
    event.add("rrule", {"freq": "weekly", "interval": 2, "until": until})
    if location.display_location:
        event.add("location", location.display_location)

    color = classify_lesson_color(lesson.subject)
    if color:
        event.add("color", color)
    _add_alarms(event)
    calendar.add_component(event)


def _add_alarms(event: Event) -> None:
    for minutes in (15, 5):
        alarm = Alarm()
        alarm.add("action", "DISPLAY")
        alarm.add("description", f"Уведомление за {minutes} минут")
        alarm.add("trigger", timedelta(minutes=-minutes))
        event.add_component(alarm)


def classify_lesson_color(subject: str) -> str | None:
    """Подбирает необязательный цвет занятия по тексту ячейки Excel."""

    if "Лекционные" in subject:
        return "orange"
    if "Практические" in subject:
        return "green"
    if "Лабораторные" in subject:
        return "blue"
    return "red"
