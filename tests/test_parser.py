from pathlib import Path

import pandas as pd
import pytest

from misis_schedule.exceptions import ScheduleParseError
from misis_schedule.models import WeekType
from misis_schedule.parser import (
    available_subgroups,
    get_groups,
    get_sheet_names,
    parse_schedule,
)


def test_reads_xls_and_xlsx(fixture_path):
    assert get_sheet_names(fixture_path) == ["Sheet1"]
    assert "1 курс" in get_sheet_names(Path("template.xls"))


def test_groups_and_variable_subgroups(fixture_sheet):
    assert get_groups(fixture_sheet) == ["G-ONE", "G-TWO", "G-THREE"]
    assert available_subgroups(fixture_sheet, "G-ONE") == [1]
    assert available_subgroups(fixture_sheet, "G-TWO") == [1, 2]
    assert available_subgroups(fixture_sheet, "G-THREE") == [1, 2, 3]


def test_parser_keeps_week_day_pair_time_and_empty_location(fixture_sheet):
    lessons = parse_schedule(fixture_sheet, "G-TWO", 1)
    assert [(lesson.week_type, lesson.subject) for lesson in lessons] == [
        (WeekType.UPPER, "Two first upper"),
        (WeekType.LOWER, "Two first lower"),
        (WeekType.UPPER, "Two first Sunday"),
        (WeekType.LOWER, "Two first lower Sunday"),
    ]
    assert lessons[0].location is None
    assert lessons[2].weekday == 6
    assert lessons[2].pair_number == 2
    assert lessons[2].start_time.isoformat() == "10:50:00"
    assert lessons[2].end_time.isoformat() == "12:25:00"


def test_missing_subgroup_never_reads_neighbour_group(fixture_sheet):
    with pytest.raises(ScheduleParseError, match="нет подгруппы 2"):
        parse_schedule(fixture_sheet, "G-ONE", 2)
    assert all(
        lesson.subject != "Two first upper" for lesson in parse_schedule(fixture_sheet, "G-ONE", 1)
    )


def test_bad_time_reports_pair_number(fixture_sheet):
    fixture_sheet.iat[2, 2] = "утром"
    with pytest.raises(ScheduleParseError, match="время пары №1"):
        parse_schedule(fixture_sheet, "G-ONE", 1)


def test_invalid_layout_has_clear_error():
    bad_sheet = pd.DataFrame(
        [["Дата", "Номер", "Время", "G"], [None] * 4, ["Понедельник", 1, "09:00 - 10:00", "x"]]
    )
    with pytest.raises(ScheduleParseError, match="структура блока"):
        available_subgroups(bad_sheet, "G")
