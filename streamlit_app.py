"""Одностраничное Streamlit-приложение для создания календаря МИСИС."""

from __future__ import annotations

import json
import re
from dataclasses import replace
from datetime import date, timedelta
from hashlib import sha256
from io import BytesIO

import pandas as pd
import streamlit as st

from misis_schedule.calendar import (
    CalendarGenerationError,
    build_calendar,
    lesson_datetime,
    validate_semester_dates,
)
from misis_schedule.exceptions import ScheduleParseError
from misis_schedule.models import Lesson
from misis_schedule.parser import (
    available_subgroups,
    get_groups,
    get_sheet_names,
    parse_schedule,
    read_sheet,
)

st.set_page_config(page_title="MISIS Schedule", page_icon="🗓️", layout="wide")


def _monday_on_or_after(value: date) -> date:
    """Возвращает ближайший понедельник, не раньше указанной даты."""

    return value + timedelta(days=(-value.weekday()) % 7)


def _preview_frame(
    lessons: list[Lesson], upper_week_start: date, lower_week_start: date
) -> pd.DataFrame:
    """Подготавливает таблицу предварительного просмотра для редактирования."""

    rows: list[dict[str, object]] = []
    for lesson in lessons:
        start, end = lesson_datetime(lesson, upper_week_start, lower_week_start)
        rows.append(
            {
                "Дата": start.date(),
                "День недели": (
                    "Понедельник",
                    "Вторник",
                    "Среда",
                    "Четверг",
                    "Пятница",
                    "Суббота",
                    "Воскресенье",
                )[lesson.weekday],
                "Неделя": lesson.week_type.label,
                "Пара": lesson.pair_number,
                "Время": f"{lesson.start_time:%H:%M}–{lesson.end_time:%H:%M}",
                "Предмет": lesson.subject,
                "Аудитория": lesson.location or "",
            }
        )
    return pd.DataFrame(rows)


def _apply_edits(lessons: list[Lesson], edited: pd.DataFrame) -> list[Lesson]:
    """Переносит разрешённые изменения из preview обратно в модели занятий."""

    return [
        replace(
            lesson,
            subject=_optional_text(row["Предмет"]) or "",
            location=_optional_text(row["Аудитория"]),
        )
        for lesson, (_, row) in zip(lessons, edited.iterrows(), strict=True)
    ]


def _optional_text(value: object) -> str | None:
    """Нормализует пустую текстовую ячейку в None."""

    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _edits_signature(lessons: list[Lesson]) -> str:
    """Возвращает хеш редактируемых полей preview для проверки актуальности ICS."""

    fields = [(lesson.subject, lesson.location) for lesson in lessons]
    payload = json.dumps(fields, ensure_ascii=False, separators=(",", ":"))
    return sha256(payload.encode()).hexdigest()


def _download_name(group_name: str, subgroup_number: int) -> str:
    """Создаёт безопасное имя скачиваемого файла."""

    normalized = re.sub(r"[^\w.-]+", "-", group_name, flags=re.UNICODE).strip("-.")
    return f"misis-{normalized or 'schedule'}-subgroup-{subgroup_number}.ics"


def main() -> None:
    """Рисует пользовательский сценарий от загрузки Excel до скачивания ICS."""

    st.title("MISIS Schedule")
    st.write("Преобразование Excel-расписания МИСИС в календарь iCalendar (.ics).")

    uploaded = st.file_uploader(
        "Загрузите файл расписания МИСИС", type=["xls", "xlsx"], key="schedule_upload"
    )
    if uploaded is None:
        return
    workbook_bytes = uploaded.getvalue()
    workbook_digest = sha256(workbook_bytes).hexdigest()

    try:
        sheet_names = get_sheet_names(BytesIO(workbook_bytes))
    except ScheduleParseError as exc:
        st.error(str(exc))
        return

    sheet_name = st.selectbox("Курс / лист расписания", sheet_names)
    try:
        sheet = read_sheet(BytesIO(workbook_bytes), sheet_name)
        groups = get_groups(sheet)
    except ScheduleParseError as exc:
        st.error(str(exc))
        return

    group_name = st.selectbox("Группа", groups)
    try:
        subgroups = available_subgroups(sheet, group_name)
    except ScheduleParseError as exc:
        st.error(str(exc))
        return

    if len(subgroups) == 1:
        subgroup_number = subgroups[0]
        st.caption(f"Подгруппа: {subgroup_number}")
    else:
        subgroup_number = st.selectbox("Подгруппа", subgroups)

    default_upper = _monday_on_or_after(date.today())
    dates_column, end_column = st.columns(2)
    with dates_column:
        upper_week_start = st.date_input("Начало верхней недели", value=default_upper)
        lower_week_start = st.date_input(
            "Начало нижней недели", value=default_upper + timedelta(days=7)
        )
    with end_column:
        semester_end = st.date_input(
            "Окончание семестра", value=default_upper + timedelta(weeks=16)
        )

    try:
        warning = validate_semester_dates(upper_week_start, lower_week_start, semester_end)
    except CalendarGenerationError as exc:
        st.error(str(exc))
        return
    if warning:
        st.warning(warning)

    try:
        lessons = parse_schedule(sheet, group_name, subgroup_number)
    except ScheduleParseError as exc:
        st.error(str(exc))
        return

    st.subheader("Расписание")
    st.write(f"Найдено занятий: {len(lessons)}")
    if not lessons:
        st.info("Для выбранной группы и подгруппы занятий не найдено.")
        return

    selection_signature = (
        workbook_digest,
        sheet_name,
        group_name,
        subgroup_number,
        upper_week_start,
        lower_week_start,
        semester_end,
    )
    edited_frame = st.data_editor(
        _preview_frame(lessons, upper_week_start, lower_week_start),
        hide_index=True,
        disabled=["Дата", "День недели", "Неделя", "Пара", "Время"],
        column_config={
            "Дата": st.column_config.DateColumn(format="DD.MM.YYYY"),
            "Пара": st.column_config.NumberColumn(format="%d"),
        },
        key="preview::" + "::".join(map(str, selection_signature)),
        use_container_width=True,
    )
    edited_lessons = _apply_edits(lessons, edited_frame)
    calendar_signature = (*selection_signature, _edits_signature(edited_lessons))
    if st.session_state.get("calendar_signature") != calendar_signature:
        st.session_state.pop("calendar_data", None)
        st.session_state.pop("calendar_name", None)
        st.session_state.pop("calendar_signature", None)

    if st.button("Сформировать календарь", type="primary"):
        try:
            calendar = build_calendar(
                edited_lessons, upper_week_start, lower_week_start, semester_end
            )
        except CalendarGenerationError as exc:
            st.error(str(exc))
        else:
            st.session_state["calendar_data"] = calendar.to_ical()
            st.session_state["calendar_name"] = _download_name(group_name, subgroup_number)
            st.session_state["calendar_signature"] = calendar_signature
            st.success("Календарь успешно сформирован.")

    if calendar_data := st.session_state.get("calendar_data"):
        st.download_button(
            "Скачать .ics",
            data=calendar_data,
            file_name=st.session_state["calendar_name"],
            mime="text/calendar",
        )


if __name__ == "__main__":
    main()
