from datetime import time

import pandas as pd

from misis_schedule.models import Lesson, WeekType
from streamlit_app import _apply_edits, _edits_signature


def test_preview_edits_clear_missing_subject_and_change_signature():
    lesson = Lesson(
        subject="Исходный предмет",
        location="А-101",
        weekday=0,
        pair_number=1,
        start_time=time(9),
        end_time=time(10, 35),
        week_type=WeekType.UPPER,
        group_name="Группа-1",
        subgroup_number=1,
    )
    edited = _apply_edits([lesson], pd.DataFrame({"Предмет": [pd.NA], "Аудитория": [float("nan")]}))

    assert edited[0].subject == ""
    assert edited[0].location is None
    assert _edits_signature([lesson]) != _edits_signature(edited)
