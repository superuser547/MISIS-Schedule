"""Generate iCalendar schedule from MISIS Excel timetable.

The script reads configuration from a `.env` file, converts the Excel
schedule into an iCalendar file and saves it to disk.  Three modes of
loading the schedule file are supported:

* ``file`` – use a local path from ``SCHEDULE_FILE_PATH``;
* ``url`` – download the file directly from ``SCHEDULE_FILE_URL``;
* ``auto`` – open ``SCHEDULE_PAGE_URL`` with Selenium and extract the
  schedule link using ``SCHEDULE_LINK_SELECTOR``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, List, Tuple

import pandas as pd
from icalendar import Alarm, Calendar, Event


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class Config:
    """Application settings loaded from environment variables."""

    group_name: str
    subgroup_number: int
    sheet_name: str
    schedule_source: str  # file, url, or auto
    schedule_file_path: str | None
    schedule_file_url: str | None
    schedule_page_url: str
    schedule_link_selector: str
    upper_week_start: str
    lower_week_start: str
    ics_filename: str


def load_config() -> Config:
    """Read settings from ``.env`` and return a :class:`Config` object."""

    try:  # импортируем только при необходимости
        from dotenv import load_dotenv
    except ImportError as exc:  # pragma: no cover - ошибка установки
        raise RuntimeError(
            "python-dotenv is required to load configuration"
        ) from exc

    load_dotenv()
    subgroup = int(os.environ.get("SUBGROUP_NUMBER", "1"))
    if subgroup not in (1, 2):
        raise ValueError("SUBGROUP_NUMBER must be 1 or 2")
    return Config(
        group_name=os.environ["GROUP_NAME"],
        subgroup_number=subgroup,
        sheet_name=os.environ["SHEET_NAME"],
        schedule_source=os.environ.get("SCHEDULE_SOURCE", "file").lower(),
        schedule_file_path=os.environ.get("SCHEDULE_FILE_PATH"),
        schedule_file_url=os.environ.get("SCHEDULE_FILE_URL"),
        schedule_page_url=os.environ.get(
            "SCHEDULE_PAGE_URL", "https://misis.ru/students/schedule/"
        ),
        schedule_link_selector=os.environ.get(
            "SCHEDULE_LINK_SELECTOR", ".col-md-2:nth-child(2) .first_child a"
        ),
        upper_week_start=os.environ["UPPER_WEEK_START"],
        lower_week_start=os.environ["LOWER_WEEK_START"],
        ics_filename=os.environ.get("ICS_FILENAME", "schedule.ics"),
    )


# ---------------------------------------------------------------------------
# Loading the schedule file
# ---------------------------------------------------------------------------


def resolve_schedule_file(cfg: Config) -> str:
    """Return a path or URL to the Excel schedule file based on ``cfg``."""

    mode = cfg.schedule_source
    if mode == "file":
        if not cfg.schedule_file_path:
            raise ValueError("SCHEDULE_FILE_PATH must be set when using file mode")
        return cfg.schedule_file_path
    if mode == "url":
        if not cfg.schedule_file_url:
            raise ValueError("SCHEDULE_FILE_URL must be set when using url mode")
        return cfg.schedule_file_url
    if mode == "auto":
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
        except Exception as exc:  # pragma: no cover - import error shown to user
            raise RuntimeError(
                "Selenium is required for 'auto' schedule mode"
            ) from exc
        driver = webdriver.Chrome()
        driver.implicitly_wait(30)
        driver.get(cfg.schedule_page_url)
        url = driver.find_element(By.CSS_SELECTOR, cfg.schedule_link_selector).get_attribute(
            "href"
        )
        driver.quit()
        return url
    raise ValueError("Unknown SCHEDULE_SOURCE. Use 'file', 'url', or 'auto'.")


# ---------------------------------------------------------------------------
# Parsing and transforming schedule data
# ---------------------------------------------------------------------------


def read_schedule(
    path_or_url: str, sheet_name: str, group_name: str, subgroup: int
) -> List[Tuple[str, str]]:
    """Load Excel schedule for ``subgroup`` and return ``(subject, room)`` tuples."""

    df = pd.read_excel(path_or_url, sheet_name=sheet_name)
    group_idx = df.columns.get_loc(group_name)
    offset = (subgroup - 1) * 2
    subjects = df.iloc[1:, group_idx + offset].tolist()
    rooms = df.iloc[1:, group_idx + offset + 1].tolist()
    data = list(zip(subjects, rooms))

    if len(data) == 97:  # expected number of slots is 98
        data.append((None, None))
    if len(data) != 98:
        raise ValueError("Ошибка при формировании информации о расписании")
    return data


def split_schedule(data: Iterable[Tuple[str, str]]) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
    """Split raw schedule data into lower and upper week lists."""

    data_list = list(data)
    return data_list[::2], data_list[1::2]


DAILY_TIMES: List[Tuple[str, str]] = [
    ("09:00", "10:35"),
    ("10:50", "12:25"),
    ("12:40", "14:15"),
    ("14:30", "16:05"),
    ("16:20", "17:55"),
    ("18:00", "19:25"),
    ("19:35", "21:00"),
]


def build_schedule_dataframe(schedule: List[Tuple[str, str]], start_date: str) -> pd.DataFrame:
    """Create a dataframe with start and end datetimes for each lesson."""

    base = datetime.fromisoformat(start_date)
    rows = []
    for i, (subject, room) in enumerate(schedule):
        day = i // 7
        pair_idx = i % 7
        start_t, end_t = DAILY_TIMES[pair_idx]
        start = datetime.strptime(f"{start_date} {start_t}", "%Y-%m-%d %H:%M") + timedelta(
            days=day
        )
        end = datetime.strptime(f"{start_date} {end_t}", "%Y-%m-%d %H:%M") + timedelta(
            days=day
        )
        rows.append({"subject": subject, "room": room, "start": start, "end": end})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Calendar generation
# ---------------------------------------------------------------------------


def create_event(cal: Calendar, subject: str, location: str, start: datetime, end: datetime, week_label: str) -> None:
    """Add a single event to ``cal``."""

    event = Event()
    event.add("summary", subject)

    day_of_week = start.weekday()  # 0 - Monday ... 6 - Sunday
    if location == "Каф. ИЯКТ":
        # Customize this block as needed. Use ``day_of_week`` and any other
        # parameters (for example, a week indicator) to replace the location
        # dynamically. Replace ``pass`` with your own logic.
        pass

    description = f"{subject}\n{location}\n{week_label}"

    if location and location.startswith("Б"):
        floor_char = location[2] if len(location) > 2 else ""
        try:
            floor = int(floor_char)
        except ValueError:
            raise ValueError("Некорректный номер этажа в корпусе Б. Проверьте настройки.")

        right_elevators = {2, 6, 9, 10}
        left_elevators = set(range(1, 12))

        if floor in right_elevators:
            description += "\nМожно использовать любой из лифтов в корпусе Б."
            location += " (Любые лифты)"
        elif floor in left_elevators:
            description += "\nМожно использовать только левые лифты в корпусе Б."
            location += " (Только левые лифты)"
        else:
            raise ValueError("Некорректный номер этажа в корпусе Б. Проверьте настройки.")

    event.add("location", location)
    event.add("description", description)
    event.add("dtstart", start)
    event.add("dtend", end)
    event.add("rrule", {"freq": "weekly", "interval": 2})

    alarm_15 = Alarm()
    alarm_15.add("action", "DISPLAY")
    alarm_15.add("description", "Уведомление за 15 минут")
    alarm_15.add("trigger", timedelta(minutes=-15))

    alarm_5 = Alarm()
    alarm_5.add("action", "DISPLAY")
    alarm_5.add("description", "Уведомление за 5 минут")
    alarm_5.add("trigger", timedelta(minutes=-5))

    event.add_component(alarm_15)
    event.add_component(alarm_5)

    if "Лекционные" in subject:
        event.add("color", "orange")
    elif "Практические" in subject:
        event.add("color", "green")
    elif "Лабораторные" in subject:
        event.add("color", "blue")
    else:
        event.add("color", "red")

    cal.add_component(event)


def write_calendar(cal: Calendar, filename: str) -> None:
    """Save calendar to ``filename`` and report whether it changed."""

    new_content = cal.to_ical()
    path = Path(filename)
    if path.exists():
        old_content = path.read_bytes()
        if old_content == new_content:
            print("Новый файл не отличается от старого. Изменения в расписании отсутствуют.")
        else:
            print("Новый файл отличается от старого. Расписание было обновлено.")
    else:
        print("Старого файла не было, сохраняем новый файл с расписанием.")

    path.write_bytes(new_content)
    print(f"Календарь создан и сохранен в файл '{filename}'")


# ---------------------------------------------------------------------------
# Main script logic
# ---------------------------------------------------------------------------


def main() -> None:
    cfg = load_config()
    schedule_path = resolve_schedule_file(cfg)
    raw_data = read_schedule(
        schedule_path, cfg.sheet_name, cfg.group_name, cfg.subgroup_number
    )
    lower, upper = split_schedule(raw_data)
    df_lower = build_schedule_dataframe(lower, cfg.lower_week_start)
    df_upper = build_schedule_dataframe(upper, cfg.upper_week_start)

    cal = Calendar()
    for df, week_label in ((df_upper, "Верхняя неделя"), (df_lower, "Нижняя неделя")):
        for _, row in df.iterrows():
            if pd.isna(row["subject"]):
                continue
            create_event(cal, row["subject"], row["room"], row["start"], row["end"], week_label)

    write_calendar(cal, cfg.ics_filename)


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()
