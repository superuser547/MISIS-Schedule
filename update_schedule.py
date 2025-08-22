import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from icalendar import Calendar, Event, Alarm

# Настройки
group_name = open("group_name.key").read()
sheet_name = open("sheet_name.key").read()
schedule_file_url = open("schedule_file_url.key").read()
use_auto_file_url = False
schedule_file_url = "/Users/usersuper/Desktop/MISIS Schedule/e54a581d43720e8803f95fa2ba88d818.xls"

if use_auto_file_url:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    driver = webdriver.Chrome()
    driver.implicitly_wait(30)
    driver.get('https://misis.ru/students/schedule/')
    schedule_file_url = driver.find_element(By.CSS_SELECTOR, ".col-md-2:nth-child(2) .first_child a").get_attribute('href')
    print(f"Auto file url: {schedule_file_url}")
    driver.quit()

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

# Вместо (старый вариант):
# lower_week_schedule = [list(x)[:2] for x in schedule[1::2]]
# upper_week_schedule = schedule[::2]

# Теперь:
lower_week_schedule = schedule[::2]  # нечётные недели идут "первыми" во втором семестре
upper_week_schedule = [list(x)[:2] for x in schedule[1::2]]


# print("---- SCHEDULE[0..10] ----")
# for i, row in enumerate(schedule[:10]):
#     print(i, row)

# print("---- LOWER_WEEK (чётные) [0..5] ----")
# for i, row in enumerate(lower_week_schedule[:5]):
#     print(i, row)

# print("---- UPPER_WEEK (нечётные) [0..5] ----")
# for i, row in enumerate(upper_week_schedule[:5]):
#     print(i, row)


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
# Вместо
# start_date_upper_week = '2024-09-02'
# start_date_lower_week = '2024-09-09'

start_date_upper_week = '2025-09-01'   # 10 февраля 2025 (понедельник)
start_date_lower_week = '2025-09-08'  # 17 февраля 2025 (понедельник)


# Добавляем временные столбцы
df_upper_week = add_time_columns(upper_week_schedule, start_date_upper_week)
df_lower_week = add_time_columns(lower_week_schedule, start_date_lower_week)

# Сдвигаем даты
df_upper_week = shift_dates_by_row(df_upper_week)
df_lower_week = shift_dates_by_row(df_lower_week)

# Функция для создания события в календаре
def create_event(cal: Calendar, subject: str, description: str, location: str, start, end):
    event = Event()
    event.add('summary', subject)

    # Пока не пишем аудиторию для английского, как пришлют - дополнить
    # Проверяем день недели и изменяем локацию, если она указана как "Каф. ИЯКТ"
    day_of_week = start.weekday()  # 0 - понедельник, 1 - вторник, ..., 6 - воскресенье
    # if location == "Каф. ИЯКТ":
    #     if day_of_week == 0:  # Понедельник
    #         location = "Б-828"
    #     elif day_of_week == 2:  # Среда
    #         location = "Б-829"
    #     else:
    #         raise ValueError("Ошибка при автоматической замене аудитории для Английского языка. Проверьте настройки")
    
    # Если аудитория находится в корпусе Б, то дополнительно добавляем в событие информацию о лифтах, которые можно использовать
    if location[0] == "Б":
        floor = location[2]

        try:
            floor = int(floor)
        except ValueError:
            raise ValueError("Некорректный номер этажа в корпусе Б. Проверьте настройки.")
        
        right_elevators = [2, 6, 9, 10]
        left_elevators = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

        if floor in right_elevators:
            description += "\nМожно использовать любой из лифтов в корпусе Б."
            location += " (Любые лифты)"
        elif floor in left_elevators:
            description += "\nМожно использовать только левые лифты в корпусе Б."
            location += " (Только левые лифты)"
        elif floor not in left_elevators:
            raise ValueError("Некорректный номер этажа в корпусе Б. Проверьте настройки.")
        
    event.add('location', location)
    event.add('description', description)

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
        create_event(cal, row['Занятие'], f"{row['Занятие']}, \n{row['Аудитория']}, \nНижняя неделя", row['Аудитория'], start, end)

# Обрабатываем каждую строку датафрейма для нижней недели
for index, row in df_lower_week.iterrows():
    if pd.notna(row['Занятие']):  # Проверяем, что занятие не пустое
        start = row['Start']
        end = row['End']
        create_event(cal, row['Занятие'], f"{row['Занятие']}, \n{row['Аудитория']}, \nВерхняя неделя", row['Аудитория'], start, end)

# # Записываем календарь в файл .ics
# with open('schedule2.ics', 'wb') as f:
#     f.write(cal.to_ical())

# print("Календарь создан и сохранен в файл 'schedule2.ics'")


# Записываем календарь в файл .ics
import os

# Генерируем контент нашего календаря в формате iCal (байты)
new_ical_content = cal.to_ical()

ics_filename = 'schedule4.ics'

# Проверяем, существует ли уже файл
if os.path.exists(ics_filename):
    # Считываем старый файл
    with open(ics_filename, 'rb') as old_file:
        old_ical_content = old_file.read()
    # Сравниваем старый и новый контент
    if old_ical_content == new_ical_content:
        print("Новый файл не отличается от старого. Изменения в расписании отсутствуют.")
    else:
        print("Новый файл отличается от старого. Расписание было обновлено.")
else:
    print("Старого файла не было, сохраняем новый файл с расписанием.")

# Перезаписываем (или создаём) файл заново
with open(ics_filename, 'wb') as f:
    f.write(new_ical_content)

print(f"Календарь создан и сохранен в файл '{ics_filename}'")
