"""Небольшой CLI-адаптер над core-кодом MISIS Schedule."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from misis_schedule.calendar import build_calendar
from misis_schedule.parser import available_subgroups, get_sheet_names, parse_schedule, read_sheet


def main() -> None:
    """Создаёт ICS из локального Excel-файла без .env и сетевой загрузки."""

    parser = argparse.ArgumentParser(description="Преобразование расписания МИСИС в .ics")
    parser.add_argument("file", type=Path, help="путь к .xls или .xlsx")
    parser.add_argument("--sheet", required=True, help="название листа Excel")
    parser.add_argument("--group", required=True, help="название академической группы")
    parser.add_argument("--subgroup", type=int, required=True, help="номер подгруппы")
    parser.add_argument("--upper-week-start", type=date.fromisoformat, required=True)
    parser.add_argument("--lower-week-start", type=date.fromisoformat, required=True)
    parser.add_argument("--semester-end", type=date.fromisoformat, required=True)
    parser.add_argument("--output", type=Path, default=Path("schedule.ics"))
    args = parser.parse_args()

    if args.sheet not in get_sheet_names(args.file):
        parser.error(f"Лист «{args.sheet}» не найден.")
    sheet = read_sheet(args.file, args.sheet)
    if args.subgroup not in available_subgroups(sheet, args.group):
        parser.error(f"Подгруппа {args.subgroup} не найдена у группы «{args.group}».")
    calendar = build_calendar(
        parse_schedule(sheet, args.group, args.subgroup),
        args.upper_week_start,
        args.lower_week_start,
        args.semester_end,
    )
    args.output.write_bytes(calendar.to_ical())
    print(f"Календарь создан: {args.output}")


if __name__ == "__main__":
    main()
