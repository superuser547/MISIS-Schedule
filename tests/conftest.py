from pathlib import Path

import pytest

from misis_schedule.parser import read_sheet


@pytest.fixture
def fixture_path() -> Path:
    """Возвращает путь к искусственному Excel fixture."""

    return Path(__file__).parent / "fixtures" / "misis_layout.xlsx"


@pytest.fixture
def fixture_sheet(fixture_path):
    """Возвращает лист искусственного расписания."""

    return read_sheet(fixture_path, "Sheet1")
