from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from icalendar import Alarm, Calendar, Event

from misis_schedule.compare import CalendarComparisonError, compare_calendars


def _calendar(*events: Event) -> bytes:
    calendar = Calendar()
    calendar.add("version", "2.0")
    for event in events:
        calendar.add_component(event)
    return calendar.to_ical()


def _event(
    uid: str,
    *,
    summary: str = "Математика",
    location: str = "А-101",
    start: datetime = datetime(2026, 9, 7, 9, 0, tzinfo=UTC),
    rrule: dict[str, object] | None = None,
    stamp: datetime = datetime(2026, 1, 1, tzinfo=UTC),
) -> Event:
    event = Event()
    event.add("uid", uid)
    event.add("dtstamp", stamp)
    event.add("summary", summary)
    event.add("dtstart", start)
    event.add("dtend", start + timedelta(minutes=90))
    event.add("location", location)
    event.add("description", f"{summary}\n{location}")
    event.add("rrule", rrule or {"freq": "weekly", "interval": 2})
    event.add("color", "red")
    alarm = Alarm()
    alarm.add("action", "DISPLAY")
    alarm.add("description", "Напоминание")
    alarm.add("trigger", timedelta(minutes=-15))
    event.add_component(alarm)
    return event


def test_equal_calendars_ignore_dtstamp() -> None:
    old = _calendar(_event("lesson-1", stamp=datetime(2026, 1, 1, tzinfo=UTC)))
    new = _calendar(_event("lesson-1", stamp=datetime(2026, 2, 1, tzinfo=UTC)))

    comparison = compare_calendars(old, new)

    assert not comparison.has_changes
    assert len(comparison.unchanged) == 1


def test_summary_change_is_modified() -> None:
    comparison = compare_calendars(
        _calendar(_event("lesson-1")), _calendar(_event("lesson-1", summary="Физика"))
    )

    assert comparison.modified[0].changed_fields == ("SUMMARY", "DESCRIPTION")


def test_location_change_is_modified() -> None:
    comparison = compare_calendars(
        _calendar(_event("lesson-1")), _calendar(_event("lesson-1", location="Б-202"))
    )

    assert comparison.modified[0].changed_fields == ("LOCATION", "DESCRIPTION")


def test_added_lesson_is_added() -> None:
    comparison = compare_calendars(_calendar(), _calendar(_event("lesson-1")))

    assert [event.uid for event in comparison.added] == ["lesson-1"]


def test_removed_lesson_is_removed() -> None:
    comparison = compare_calendars(_calendar(_event("lesson-1")), _calendar())

    assert [event.uid for event in comparison.removed] == ["lesson-1"]


def test_rrule_and_time_changes_are_modified() -> None:
    comparison = compare_calendars(
        _calendar(_event("lesson-1")),
        _calendar(
            _event(
                "lesson-1",
                start=datetime(2026, 9, 7, 10, 0, tzinfo=UTC),
                rrule={"freq": "weekly", "interval": 1},
            )
        ),
    )

    assert comparison.modified[0].changed_fields == ("DTSTART", "DTEND", "RRULE")


def test_invalid_ics_is_reported() -> None:
    with pytest.raises(CalendarComparisonError, match="Не удалось прочитать"):
        compare_calendars(b"not a calendar", _calendar())
