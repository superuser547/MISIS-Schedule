from dataclasses import replace
from datetime import date, time

import pytest
from icalendar import Calendar

from misis_schedule.calendar import MOSCOW_TZ, build_calendar, stable_uid, validate_semester_dates
from misis_schedule.exceptions import CalendarGenerationError
from misis_schedule.models import Lesson, WeekType


@pytest.fixture
def lesson():
    return Lesson(
        subject="Математика (Практические)",
        location="Б-434",
        weekday=0,
        pair_number=1,
        start_time=time(9),
        end_time=time(10, 35),
        week_type=WeekType.UPPER,
        group_name="Группа-1",
        subgroup_number=2,
    )


def test_calendar_has_required_properties_timezone_recurrence_and_alarms(lesson):
    calendar = build_calendar([lesson], date(2026, 9, 7), date(2026, 9, 14), date(2026, 12, 31))
    parsed = Calendar.from_ical(calendar.to_ical())
    assert str(parsed["VERSION"]) == "2.0"
    assert str(parsed["PRODID"]) == "-//MISIS Schedule//RU"
    assert str(parsed["CALSCALE"]) == "GREGORIAN"
    event = parsed.walk("VEVENT")[0]
    assert event.decoded("DTSTART").tzinfo == MOSCOW_TZ
    assert event.decoded("DTSTART").hour == 9
    assert event.decoded("DTEND").minute == 35
    assert event["RRULE"]["FREQ"] == ["WEEKLY"]
    assert event["RRULE"]["INTERVAL"] == [2]
    assert event["RRULE"]["UNTIL"][0].date() == date(2026, 12, 31)
    assert str(event["LOCATION"]).startswith("Б-434")
    assert [
        alarm["TRIGGER"].to_ical().decode()
        for alarm in event.subcomponents
        if alarm.name == "VALARM"
    ] == [
        "-PT15M",
        "-PT5M",
    ]


def test_uid_is_stable_when_text_changes(lesson):
    autumn = (date(2026, 9, 7), date(2026, 9, 14))
    spring = (date(2027, 2, 8), date(2027, 2, 15))
    assert stable_uid(lesson, *autumn) == stable_uid(
        replace(lesson, subject="Другая дисциплина"), *autumn
    )
    assert stable_uid(lesson, *autumn) == stable_uid(replace(lesson, location="А-101"), *autumn)
    assert stable_uid(lesson, *autumn) != stable_uid(lesson, *spring)


def test_empty_location_is_omitted_and_empty_subject_is_skipped(lesson):
    calendar = build_calendar(
        [replace(lesson, location=None), replace(lesson, subject=" ")],
        date(2026, 9, 7),
        date(2026, 9, 14),
        date(2026, 12, 31),
    )
    events = calendar.walk("VEVENT")
    assert len(events) == 1
    assert events[0].get("LOCATION") is None


def test_dates_must_start_on_monday_and_end_later():
    with pytest.raises(CalendarGenerationError, match="понедельник"):
        validate_semester_dates(date(2026, 9, 8), date(2026, 9, 14), date(2026, 12, 31))
    with pytest.raises(CalendarGenerationError, match="окончания"):
        validate_semester_dates(date(2026, 9, 7), date(2026, 9, 14), date(2026, 9, 14))
