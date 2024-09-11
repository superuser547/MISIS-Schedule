import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from icalendar import Calendar, Event, Alarm

# Настройки
group_name = "ББИ-24-3"
sheet_name = "1 курс"
schedule_file_url = "https://misis.ru/files/-/715c2b5e46318098d84f36722b9532dd/10924_ikn.xlsx"
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
# list3 = df[df.columns[group_column_indexes[2]]].tolist()[1:]
# list4 = df[df.columns[group_column_indexes[3]]].tolist()[1:]

data = [list(item) for item in zip(list1, list2)]
# data = [list(item) for item in zip(list1, list2, list3, list4)]

if len(data) == 97: # 98 - константное число "окон" в течение недели (7 пар в день * 7 дней в неделю * 2 части в паре)
    data.append([np.nan, np.nan, np.nan, np.nan]) # добавляем последнюю часть пары в воскресенье, если она не заполнена
else:
    raise ValueError("Ошибка при формировании информации о расписании")

# Ваш список занятий
schedule = data

# Разделение на верхнюю и нижнюю неделю
# upper_week_schedule = [row[:2] for row in schedule]  # Первые два столбца для верхней недели
# lower_week_schedule = [row[2:] for row in schedule]  # Последние два столбца для нижней недели

lower_week_schedule = [list(x)[:2] for x in schedule[1::2]]  # Элементы с нечетными индексами
upper_week_schedule = schedule[::2]  # Элементы с четными индексами

# Преобразуем списки в DataFrame и добавляем временные метки начала и конца пар
schedule_times = [
    ("09:00:00", "10:35:00"),
    ("10:50:00", "12:25:00"),
    ("12:40:00", "14:15:00"),
    ("14:30:00", "16:05:00"),
    ("16:20:00", "17:55:00"),
    ("18:00:00", "19:25:00"),
    ("19:35:00", "21:00:00"),
    
    ("09:00:00", "10:35:00"),
    ("10:50:00", "12:25:00"),
    ("12:40:00", "14:15:00"),
    ("14:30:00", "16:05:00"),
    ("16:20:00", "17:55:00"),
    ("18:00:00", "19:25:00"),
    ("19:35:00", "21:00:00"),

    ("09:00:00", "10:35:00"),
    ("10:50:00", "12:25:00"),
    ("12:40:00", "14:15:00"),
    ("14:30:00", "16:05:00"),
    ("16:20:00", "17:55:00"),
    ("18:00:00", "19:25:00"),
    ("19:35:00", "21:00:00"),

    ("09:00:00", "10:35:00"),
    ("10:50:00", "12:25:00"),
    ("12:40:00", "14:15:00"),
    ("14:30:00", "16:05:00"),
    ("16:20:00", "17:55:00"),
    ("18:00:00", "19:25:00"),
    ("19:35:00", "21:00:00"),

    ("09:00:00", "10:35:00"),
    ("10:50:00", "12:25:00"),
    ("12:40:00", "14:15:00"),
    ("14:30:00", "16:05:00"),
    ("16:20:00", "17:55:00"),
    ("18:00:00", "19:25:00"),
    ("19:35:00", "21:00:00"),

    ("09:00:00", "10:35:00"),
    ("10:50:00", "12:25:00"),
    ("12:40:00", "14:15:00"),
    ("14:30:00", "16:05:00"),
    ("16:20:00", "17:55:00"),
    ("18:00:00", "19:25:00"),
    ("19:35:00", "21:00:00"),

    ("09:00:00", "10:35:00"),
    ("10:50:00", "12:25:00"),
    ("12:40:00", "14:15:00"),
    ("14:30:00", "16:05:00"),
    ("16:20:00", "17:55:00"),
    ("18:00:00", "19:25:00"),
    ("19:35:00", "21:00:00"),
]


def add_time_columns(schedule, start_date):
    df_schedule = pd.DataFrame(schedule, columns=['Занятие', 'Аудитория'])
    df_schedule['Start'] = None
    df_schedule['End'] = None
    
    # Убедитесь, что количество строк в df_schedule не превышает количество элементов в schedule_times
    num_rows = min(len(df_schedule), len(schedule_times))
    
    for i in range(num_rows):
        times = schedule_times[i]
        start_time_str = f"{start_date} {times[0]}"
        end_time_str = f"{start_date} {times[1]}"
        
        start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
        
        df_schedule.at[i, 'Start'] = start_time
        df_schedule.at[i, 'End'] = end_time
    
    return df_schedule

def shift_dates_by_row(df: pd.DataFrame):
    # Определяем количество дней для каждого ряда
    df['days_to_add'] = df.index // 7

    # Добавляем дни к столбцам Start и End
    df['Start'] = pd.to_datetime(df['Start']) + pd.to_timedelta(df['days_to_add'], unit='D')
    df['End'] = pd.to_datetime(df['End']) + pd.to_timedelta(df['days_to_add'], unit='D')

    # Убираем вспомогательный столбец days_to_add
    df = df.drop(columns=['days_to_add'])
    
    return df

# Даты начала верхней и нижней недель
start_date_upper_week = '2024-09-02'
start_date_lower_week = '2024-09-09'

# Добавляем временные столбцы
df_upper_week = add_time_columns(upper_week_schedule, start_date_upper_week)
df_lower_week = add_time_columns(lower_week_schedule, start_date_lower_week)

# Сдвигаем даты
df_upper_week = shift_dates_by_row(df_upper_week)
df_lower_week = shift_dates_by_row(df_lower_week)

# Функция для создания события в календаре
def create_event(cal, subject, description, location, start, end):
    event = Event()
    event.add('summary', subject)
    event.add('description', description)

    # Проверяем день недели и изменяем локацию, если она указана как "Каф. ИЯКТ"
    day_of_week = start.weekday()  # 0 - понедельник, 1 - вторник, ..., 6 - воскресенье
    if location == "Каф. ИЯКТ":
        if day_of_week == 1:  # Вторник
            location = "Г-460"
        elif day_of_week == 3:  # Четверг
            location = "Г-473"
        else:
            raise ValueError("Ошибка при автоматической замене аудитории для Английского языка. Проверьте настройки")
    
    event.add('location', location)

    event.add('dtstart', start)
    event.add('dtend', end)
    
    # Добавляем повторение каждые 2 недели
    event.add('rrule', {'freq': 'weekly', 'interval': 2})

    # Добавляем уведомления за 15 и 5 минут
    alarm_15_min = Alarm()
    alarm_15_min.add('action', 'DISPLAY')
    alarm_15_min.add('description', "Уведомление за 15 минут")
    alarm_15_min.add('trigger', timedelta(minutes=-15))
    
    alarm_5_min = Alarm()
    alarm_5_min.add('action', 'DISPLAY')
    alarm_5_min.add('description', "Уведомление за 5 минут")
    alarm_5_min.add('trigger', timedelta(minutes=-5))

    event.add_component(alarm_15_min)
    event.add_component(alarm_5_min)

    # Определяем цвет события через свойство COLOR
    if "Лекционные" in subject:
        event.add('color', 'orange')  # Оранжевый цвет для лекций
    elif "Практические" in subject:
        event.add('color', 'green')  # Зеленый цвет для практик
    elif "Лабораторные" in subject:
        event.add('color', 'blue')  # Синий цвет для лабораторных
    else:
        event.add('color', 'red')  # Красный цвет для остальных событий

    cal.add_component(event)

# Создаем пустой календарь
cal = Calendar()

# Обрабатываем каждую строку датафрейма для верхней недели
for index, row in df_upper_week.iterrows():
    if pd.notna(row['Занятие']):  # Проверяем, что занятие не пустое
        start = row['Start']
        end = row['End']
        create_event(cal, row['Занятие'], f"{row['Занятие']}, \n{row['Аудитория']}, \nВерхняя неделя", row['Аудитория'], start, end)

# Обрабатываем каждую строку датафрейма для нижней недели
for index, row in df_lower_week.iterrows():
    if pd.notna(row['Занятие']):  # Проверяем, что занятие не пустое
        start = row['Start']
        end = row['End']
        create_event(cal, row['Занятие'], f"{row['Занятие']}, \n{row['Аудитория']}, \nНижняя неделя", row['Аудитория'], start, end)

# Записываем календарь в файл .ics
with open('schedule.ics', 'wb') as f:
    f.write(cal.to_ical())

print("Календарь создан и сохранен в файл 'schedule.ics'")
