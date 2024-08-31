import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from icalendar import Calendar, Event

# Настройки
group_name = "ББИ-24-3"
sheet_name = "1 курс"
schedule_file_url = "https://misis.ru/files/-/676a0ea59835a0f6ee2bac376fb7e899/ikn_300824.xlsx"
# schedule_file_path = "ikn_300824.xlsx"

df = pd.read_excel(schedule_file_url, sheet_name=sheet_name)


group_column_indexes = [
    df.columns.get_loc(group_name),
    df.columns.get_loc(group_name) + 1,
    df.columns.get_loc(group_name) + 2,
    df.columns.get_loc(group_name) + 3
]

list1 = df[df.columns[group_column_indexes[0]]].tolist()[1:]
list2 = df[df.columns[group_column_indexes[1]]].tolist()[1:]
list3 = df[df.columns[group_column_indexes[2]]].tolist()[1:]
list4 = df[df.columns[group_column_indexes[3]]].tolist()[1:]

data = [list(item) for item in zip(list1, list2, list3, list4)]

if len(data) == 97: # 98 - константное число "окон" в течение недели (7 пар в день * 7 дней в неделю * 2 части в паре)
    data.append([np.nan, np.nan, np.nan, np.nan]) # добавляем последнюю часть пары в воскресенье, если она не заполнена
else:
    raise ValueError("Ошибка при формировании информации о расписании")

# Ваш список занятий
schedule = data

# Разделение на верхнюю и нижнюю неделю
upper_week_schedule = [row[:2] for row in schedule]  # Первые два столбца для верхней недели
lower_week_schedule = [row[2:] for row in schedule]  # Последние два столбца для нижней недели

# Даты начала верхней и нижней недель
start_date_upper_week = datetime(2024, 9, 2, 9, 0)  # 2 сентября 2024 - начало верхней недели
start_date_lower_week = datetime(2024, 9, 9, 9, 0)  # 9 сентября 2024 - начало нижней недели

# Функция для создания временных интервалов с учетом перерывов
def create_time_intervals(start_date):
    time_intervals = []
    days_of_week = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    lesson_durations = timedelta(minutes=45)
    short_break = timedelta(minutes=5)
    long_break = timedelta(minutes=15)

    for day in range(7):  # 7 дней в неделе
        current_time = start_date + timedelta(days=day)
        for lesson in range(7):  # 7 пар
            # Начало и конец первой половины пары
            start_time = current_time
            end_time = current_time + lesson_durations
            time_intervals.append((start_time, end_time, days_of_week[day]))
            
            # Обновление времени с учетом короткого перерыва
            current_time = end_time + short_break
            
            # Начало и конец второй половины пары
            start_time = current_time
            end_time = current_time + lesson_durations
            time_intervals.append((start_time, end_time, days_of_week[day]))
            
            # Обновление времени с учетом длинного перерыва между парами
            current_time = end_time + long_break
            
    return time_intervals

# Создание временных интервалов для верхней и нижней недель
time_intervals_upper_week = create_time_intervals(start_date_upper_week)
time_intervals_lower_week = create_time_intervals(start_date_lower_week)

# Добавление временных интервалов к расписанию
for i, row in enumerate(upper_week_schedule):
    start, end, day = time_intervals_upper_week[i]
    upper_week_schedule[i].extend([start.strftime('%Y-%m-%d %H:%M'), end.strftime('%Y-%m-%d %H:%M'), day])

for i, row in enumerate(lower_week_schedule):
    start, end, day = time_intervals_lower_week[i]
    lower_week_schedule[i].extend([start.strftime('%Y-%m-%d %H:%M'), end.strftime('%Y-%m-%d %H:%M'), day])

# Создаем календарь
cal = Calendar()

# Функция для создания события
def create_event(summary, description, location, start, end, freq, interval, color):
    event = Event()
    event.add('summary', summary)
    event.add('description', description)
    event.add('location', location)
    event.add('dtstart', start)
    event.add('dtend', end)
    event.add('rrule', {'freq': freq, 'interval': interval})
    event.add('color', color)  # Добавление цвета события
    return event

# Функция для определения типа занятия и выбора цвета
def get_event_color(title):
    if 'Лекционные' in title:
        return '#FF5733'  # Оранжевый для лекционных
    elif 'Практические' in title:
        return '#33FF57'  # Зеленый для практических
    elif 'Лабораторные' in title:
        return '#3357FF'  # Синий для лабораторных
    else:
        return '#FC0303'  # Красный для остальных

# Заполнение календаря событиями для верхней недели
for row in upper_week_schedule:
    if (row[0]) and (row[0] != 'nan') and (row[0] != np.nan) and (type(row[0]) == str) and (row[1]) and (row[1] != 'nan') and (row[1] != np.nan) and (type(row[1]) == str):
        color = get_event_color(row[0])  # Определение цвета события
        event_upper = create_event(
            row[0],
            f'{row[0]} - {row[1]} \nВерхняя неделя',
            row[1],
            datetime.strptime(row[2], '%Y-%m-%d %H:%M'),
            datetime.strptime(row[3], '%Y-%m-%d %H:%M'),
            'WEEKLY', 2,
            color
        )
        cal.add_component(event_upper)

# Заполнение календаря событиями для нижней недели
for row in lower_week_schedule:
    if (row[0]) and (row[0] != 'nan') and (row[0] != np.nan) and (type(row[0]) == str) and (row[1]) and (row[1] != 'nan') and (row[1] != np.nan) and (type(row[1]) == str):
        color = get_event_color(row[0])  # Определение цвета события
        event_lower = create_event(
            row[0],
            f'{row[0]} - {row[1]} \nНижняя неделя',
            row[1],
            datetime.strptime(row[2], '%Y-%m-%d %H:%M'),
            datetime.strptime(row[3], '%Y-%m-%d %H:%M'),
            'WEEKLY', 2,
            color
        )
        cal.add_component(event_lower)

# Сохранение в файл
with open('schedule.ics', 'wb') as f:
    f.write(cal.to_ical())

print("Календарь создан и сохранен как 'schedule.ics'")