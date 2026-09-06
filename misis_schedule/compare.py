"""Семантическое сравнение календарей iCalendar."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from icalendar import Calendar, Event


class CalendarComparisonError(ValueError):
    """Календарь нельзя разобрать или сопоставить с другим календарём."""


ChangeKind = Literal["added", "removed", "modified", "unchanged"]
_FIELDS = ("SUMMARY", "DTSTART", "DTEND", "LOCATION", "DESCRIPTION", "RRULE", "COLOR")


@dataclass(frozen=True)
class EventComparison:
    """Результат сравнения одного события с тем же UID в другом календаре."""

    uid: str
    status: ChangeKind
    summary: str
    changed_fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class CalendarComparison:
    """Результат сопоставления всех VEVENT двух календарей."""

    events: tuple[EventComparison, ...]

    @property
    def added(self) -> tuple[EventComparison, ...]:
        return self._with_status("added")

    @property
    def removed(self) -> tuple[EventComparison, ...]:
        return self._with_status("removed")

    @property
    def modified(self) -> tuple[EventComparison, ...]:
        return self._with_status("modified")

    @property
    def unchanged(self) -> tuple[EventComparison, ...]:
        return self._with_status("unchanged")

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.modified)

    def _with_status(self, status: ChangeKind) -> tuple[EventComparison, ...]:
        return tuple(event for event in self.events if event.status == status)


def compare_calendars(old_ics: bytes | str, new_ics: bytes | str) -> CalendarComparison:
    """Сравнивает VEVENT двух ICS по UID, игнорируя технические поля вроде DTSTAMP."""

    old_events = _events_by_uid(_parse_calendar(old_ics, "предыдущий"))
    new_events = _events_by_uid(_parse_calendar(new_ics, "новый"))
    comparisons: list[EventComparison] = []

    for uid in sorted(old_events.keys() | new_events.keys()):
        old_event = old_events.get(uid)
        new_event = new_events.get(uid)
        if old_event is None:
            comparisons.append(EventComparison(uid, "added", _summary(new_event)))
        elif new_event is None:
            comparisons.append(EventComparison(uid, "removed", _summary(old_event)))
        else:
            changed_fields = _changed_fields(old_event, new_event)
            comparisons.append(
                EventComparison(
                    uid,
                    "modified" if changed_fields else "unchanged",
                    _summary(new_event),
                    changed_fields,
                )
            )
    return CalendarComparison(tuple(comparisons))


def _parse_calendar(ics: bytes | str, label: str) -> Calendar:
    try:
        calendar = Calendar.from_ical(ics)
    except (TypeError, ValueError, KeyError) as exc:
        raise CalendarComparisonError(f"Не удалось прочитать {label} .ics-файл.") from exc
    if not isinstance(calendar, Calendar) or calendar.name != "VCALENDAR":
        raise CalendarComparisonError(f"{label.capitalize()} файл не является календарём .ics.")
    return calendar


def _events_by_uid(calendar: Calendar) -> dict[str, Event]:
    events: dict[str, Event] = {}
    for component in calendar.walk("VEVENT"):
        uid_property = component.get("UID")
        if uid_property is None:
            raise CalendarComparisonError("В календаре найдено событие без UID.")
        uid = str(uid_property)
        if uid in events:
            raise CalendarComparisonError(f"В календаре найден повторяющийся UID: {uid}.")
        events[uid] = component
    return events


def _changed_fields(old_event: Event, new_event: Event) -> tuple[str, ...]:
    changed = [
        field
        for field in _FIELDS
        if _property_value(old_event, field) != _property_value(new_event, field)
    ]
    if _alarms(old_event) != _alarms(new_event):
        changed.append("VALARM")
    return tuple(changed)


def _property_value(event: Event, name: str) -> bytes | None:
    value = event.get(name)
    return value.to_ical() if value is not None else None


def _alarms(event: Event) -> tuple[tuple[tuple[str, bytes], ...], ...]:
    alarms = []
    for alarm in event.subcomponents:
        if alarm.name != "VALARM":
            continue
        properties = tuple(
            sorted(
                (name, value.to_ical())
                for name, value in alarm.items()
                if name != "DTSTAMP"
            )
        )
        alarms.append(properties)
    return tuple(sorted(alarms))


def _summary(event: Event | None) -> str:
    if event is None:
        return "Без названия"
    return str(event.get("SUMMARY", "Без названия"))
