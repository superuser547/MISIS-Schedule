"""Исключения предметной области приложения."""


class ScheduleError(Exception):
    """Базовая ошибка обработки расписания."""


class ScheduleParseError(ScheduleError):
    """Ошибка разбора Excel-расписания."""


class CalendarGenerationError(ScheduleError):
    """Ошибка формирования календаря."""
