# Переводим список в строку, чтобы записать в таблицу.
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



