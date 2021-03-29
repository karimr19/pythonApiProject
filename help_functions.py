# Переводим список в строку, чтобы записать в таблицу.
import re


def list_to_string(input_list):
    output = ''
    for j in range(len(input_list) - 1):
        output += str(input_list[j]) + ' '
    if len(input_list) != 0:
        output += str(input_list[len(input_list) - 1])
    return output


# Считает рейтинг курьера.
def count_rating(region_dict):
    average_region_time = []
    for region in region_dict:
        sum_of_seconds = 0
        for time in region_dict[region]:
            sum_of_seconds += time
        average_region_time.append(int(sum_of_seconds / len(region_dict[region])))
    return ((60 * 60 - min(60 * 60, min(average_region_time))) / (60 * 60)) * 5


# Функция возвращает список списков с часами и минутами.
def time_list(time_intervals):
    hour_minute_list = []
    # На вход нам дан список строк вида "10:00-18:00".
    for interval in time_intervals:
        # Разделяем строку на начальное и конечное время.
        time_interval = list(map(str, interval.split('-')))
        for time in time_interval:
            # Разбиваем начальное и конечное время на часы и минуты.
            hour_minute_list.append(list(map(int, time.split(':'))))
    return hour_minute_list


# Проверяем корректность типов данных при добавлении заказа.
def validate_order_input_type(input_dict):
    if (((type(input_dict['weight']) == int or type(input_dict['weight']) == float) and
         0.01 <= input_dict['weight'] <= 50) and (
            (type(input_dict['region']) == int) and (input_dict['region'] > 0))
            and (type(input_dict["delivery_hours"]) == list and all(type(i) == str for i in input_dict['delivery_hours'])
                 and
                 all(re.fullmatch(r'\d{2}:\d{2}-\d{2}:\d{2}', interval) for interval in input_dict["delivery_hours"]))):
        hours_minutes_list = time_list(input_dict["delivery_hours"])
        return validate_time_list(hours_minutes_list)
    return False


# Проверяем, что информация переданная в запросе изменить курьера корректна.
def validate_courier_edit(input_dict):
    # Проверяем, что инфа про регионы корректна.
    if 'regions' in input_dict:
        if not ((type(input_dict['regions']) == list) and
                (all((type(input_dict['regions'][i]) == int) for i
                     in range(len(input_dict['regions']))))):
            return False
    # Проверяем, что инфа про тип курьера корректна.
    if 'courier_type' in input_dict and not (input_dict['courier_type'] in ['foot', 'bike', 'car']):
        return False
    # Проверяем, что инфа про часы работы корректна.
    if 'working_hours' in input_dict and not (
            (type(input_dict["working_hours"]) == list and all(type(i) == str for i in input_dict['working_hours'])
             and
             all(re.fullmatch(r'\d{2}:\d{2}-\d{2}:\d{2}', interval) for interval
                 in input_dict["working_hours"])) and validate_time_list(time_list(input_dict["working_hours"]))):
        return False
    return True


# Проверяем корректность типов данных при добавлении курьера.
def validate_courier_input_type(input_dict):
    # Проверяем корректность типа курьера.
    if ((input_dict['courier_type'] in ['foot', 'bike', 'car']) and
            # Проверяем корректность регионов работы.
            ((type(input_dict['regions']) == list) and (all((type(input_dict['regions'][i]) == int)
                                                            for i in range(len(input_dict['regions']))))) and
            # Проверяем корректность часов работы.
            (type(input_dict["working_hours"]) == list and all(type(i) == str for i in input_dict['working_hours'])
             and all(re.fullmatch(r'\d{2}:\d{2}-\d{2}:\d{2}', interval) for interval
                     in input_dict["working_hours"]))):
        hours_minutes_list = time_list(input_dict["working_hours"])
        return validate_time_list(hours_minutes_list)
    return False


# Проверяет, что время задано корректно.
def validate_time_list(hours_minutes_list):
    is_correct = True
    # Проверяем корректность времени.
    for i in range(0, len(hours_minutes_list)):
        if hours_minutes_list[i][0] > 23 or hours_minutes_list[i][0] < 0:
            is_correct = False
            break
        if hours_minutes_list[i][1] > 59 or hours_minutes_list[i][1] < 0:
            is_correct = False
            break
    if is_correct:
        # Проверяем, чтобы левая граница была меньше правой.
        for i in range(0, len(hours_minutes_list), 2):
            left = hours_minutes_list[i][0] * 100 + hours_minutes_list[i][1]
            right = hours_minutes_list[i + 1][0] * 100 + hours_minutes_list[i + 1][1]
            if left >= right:
                is_correct = False
                break
    return is_correct
