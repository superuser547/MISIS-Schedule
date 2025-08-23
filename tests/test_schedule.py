from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from generate_schedule import build_schedule_dataframe, read_schedule, split_schedule


def test_split_schedule():
    data = [(f"sub{i}", f"room{i}") for i in range(6)]
    lower, upper = split_schedule(data)
    assert lower == [("sub0", "room0"), ("sub2", "room2"), ("sub4", "room4")]
    assert upper == [("sub1", "room1"), ("sub3", "room3"), ("sub5", "room5")]


def test_build_schedule_dataframe():
    schedule = [("Math", "B-100")] * 14  # two days of schedule
    df = build_schedule_dataframe(schedule, "2024-09-02")
    assert len(df) == len(schedule)
    assert df.iloc[0]["start"] == datetime(2024, 9, 2, 9, 0)
    assert df.iloc[1]["end"] == datetime(2024, 9, 2, 12, 25)
    assert df.iloc[7]["start"] == datetime(2024, 9, 3, 9, 0)


def test_read_schedule_subgroup(tmp_path):
    import pandas as pd

    data = {
        "Group": [1] + [f"S1_{i}" for i in range(98)],
        "Room1": [""] + [f"R1_{i}" for i in range(98)],
        "Group.1": [2] + [f"S2_{i}" for i in range(98)],
        "Room2": [""] + [f"R2_{i}" for i in range(98)],
    }
    file = tmp_path / "schedule.xlsx"
    pd.DataFrame(data).to_excel(file, index=False)

    sub1 = read_schedule(str(file), "Sheet1", "Group", 1)
    sub2 = read_schedule(str(file), "Sheet1", "Group", 2)

    assert sub1[0] == ("S1_0", "R1_0")
    assert sub2[0] == ("S2_0", "R2_0")
