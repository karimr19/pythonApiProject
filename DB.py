import sqlite3
from sqlite3 import Error
import dateutil.parser
import help_functions


# Словарь для перевода типа курьера в грузоподъёмность.
weight_dict = {'foot': 10, 'bike': 15, 'car': 50}


def sql_connection():
    try:
        local_con = sqlite3.connect('Couriers.db')
        return local_con
    except Error:
        print(Error)


# Создаем таблицу с курьерами, если она еще не была создана.
def create_couriers_table():
    with sql_connection() as local_con:
        cur = local_con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS couriers(courier_id integer PRIMARY KEY, courier_type text, "
                    "regions text, working_hours text)")
        local_con.commit()


# Создаем таблицу с заказами, если она еще не была создана.
def create_orders_table():
    with sql_connection() as local_con:
        cur = local_con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS orders(order_id integer PRIMARY KEY, weight real, "
                    "region int, delivery_hours text, executing_courier_id integer default 0, completed bool "
                    "default false, start text, end text, courier_type text)")
        local_con.commit()


# Добавляем курьеров в таблицу.
def insert_couriers(entities):
    with sql_connection() as local_con:
        cur = local_con.cursor()
        cur.execute('INSERT INTO couriers(courier_id, courier_type, regions, working_hours) VALUES(?, ?, ?, ?)',
                    entities)
        local_con.commit()


# Добавляем заказы в таблицу.
def insert_orders(entities):
    with sql_connection() as local_con:
        cur = local_con.cursor()
        cur.execute('INSERT INTO orders(order_id, weight, region, delivery_hours) VALUES(?, ?, ?, ?)',
                    entities)
        local_con.commit()


# Изменяем данные в таблице курьеров.
def couriers_table_update(courier_id, column_name, value):
    with sql_connection() as local_con:
        cur = local_con.cursor()
        if column_name == 'regions':
            cur.execute('UPDATE couriers SET regions = ? WHERE courier_id = ?', (help_functions.list_to_string(value),
                                                                                 int(courier_id)))
        elif column_name == 'working_hours':
            cur.execute('UPDATE couriers SET working_hours = ? WHERE courier_id = ?',
                        (help_functions.list_to_string(value), int(courier_id)))
        else:
            cur.execute('UPDATE couriers SET courier_type = ? WHERE courier_id = ?', (value, int(courier_id)))
        local_con.commit()


# Получаем информацию о курьере с заданным id из таблицы с курьерами.
def courier_info(courier_id):
    with sql_connection() as local_con:
        cur = local_con.cursor()
        cur.execute('SELECT * FROM couriers WHERE courier_id = ?', (int(courier_id),))
        # Создаем словарь из выбранной строки.
        r = dict((cur.description[i][0], value) for i, value in enumerate(cur.fetchone()))
        return r


# Возвращает список невыполненных и неназначенных заказов с массой меньше грузоподъёмности.
def orders_to_assign(max_weight):
    with sql_connection() as local_con:
        cur = local_con.cursor()
        # Считываем неназначенные, невыполненные заказы, масса которых не больше грузоподъёмности конкретного
        # курьера.
        cur.execute('SELECT order_id, delivery_hours, region FROM orders WHERE executing_courier_id = 0 AND '
                    'completed = false AND weight <= ?', (max_weight,))
        return [dict((cur.description[i][0], value) for i, value in enumerate(row)) for row in cur.fetchall()]


# Получаем заказы с заданным исполняющим курьером.
def orders_info(courier_id):
    with sql_connection() as local_con:
        cur = local_con.cursor()
        cur.execute('SELECT order_id, region, start, end, courier_type FROM orders WHERE executing_courier_id = ? '
                    'AND completed = true', (courier_id,))
        return [dict((cur.description[i][0], value) for i, value in enumerate(row)) for row in cur.fetchall()]


# Проверка существования курьера с заданным id в таблице с курьерами.
def courier_exists(courier_id):
    with sql_connection() as local_con:
        cur = local_con.cursor()
        return bool(cur.execute('SELECT * FROM couriers WHERE courier_id = ?', (courier_id,)).fetchall())


# Проверка существования заказа с заданным id в таблице с заказами.
def order_exists(order_id):
    with sql_connection() as local_con:
        cur = local_con.cursor()
        return bool(cur.execute('SELECT * FROM orders WHERE order_id = ?', (order_id,)).fetchall())


# Проверка соответствия заказа.
def validate_order(order_id, courier_id, end_time_string):
    with sql_connection() as local_con:
        cur = local_con.cursor()
        # Проверяем, что в таблице есть заказ с соответствующими параметрами.
        if bool(cur.execute('SELECT * FROM orders WHERE order_id = ? AND executing_courier_id = ? AND '
                            'completed = false', (order_id, courier_id)).fetchall()):
            # Выделяем время начала заказа.
            cur.execute('SELECT start FROM orders WHERE order_id = ?', (order_id,))
            # Считываем время начала заказа.
            order_dict = dict((cur.description[0][i], value) for i, value in enumerate(cur.fetchone()))
            # Проверяем, что время заказа не пустое.
            if len(order_dict) != 0 and order_dict['start'] != '' and order_dict['start'] is not None:
                start_time = dateutil.parser.isoparse(order_dict['start'])
                end_time = dateutil.parser.isoparse(end_time_string)
                # Проверяем, что конец заказа произошел после начала заказа.
                if end_time > start_time:
                    return True
    return False


# Изменяет таблицу заказов.
def orders_table_update(courier_id):
    # Считываем информацию о курьере.
    courier_info_dict = courier_info(courier_id)
    match_orders = []
    # Проверяем, что у курьера есть часы работы и регионы.
    if courier_info_dict['working_hours'] != '' and courier_info_dict['regions'] != '':
        # Считываем тнтервалы времени.
        time_intervals = list(map(str, courier_info_dict['working_hours'].split()))
        # Получаем список часов работы курьеров вида: [[часы, минуты], [часы, минуты]], [[...
        courier_hours_minutes_list = help_functions.time_list(time_intervals)
        # Регионы где работает курьер.
        regions = list(map(int, courier_info_dict['regions'].split()))
        # Смотрим грузоподьёмность курьера.
        max_weight = weight_dict[courier_info_dict['courier_type']]
        with sql_connection() as local_con:
            cur = local_con.cursor()
            # Выделяем в таблице заказов невыполненные заказы, которые исполняет заданный курьер.
            cur.execute('SELECT order_id, delivery_hours, region, weight FROM orders WHERE executing_courier_id = ? '
                        'AND completed = false', (courier_id,))
            # Считываем выделенные заказы в виде словарей.
            orders_info_list = [dict((cur.description[i][0], value) for i, value in enumerate(row)) for row in
                                cur.fetchall()]
            # Проверяем, нашлись ли заказы.
            if len(orders_info_list) != 0:
                # Проходим по всем заказам.
                for order in orders_info_list:
                    # Меняем данные заказа, если он перестал подходить с новыми параметрами курьера.
                    if not normal_order(order, regions, max_weight, courier_hours_minutes_list):
                        cur.execute('UPDATE orders SET executing_courier_id = 0, start = ?, courier_type = ? WHERE '
                                    'order_id = ?', ('', '', order['order_id']))
                        local_con.commit()


# Изменяем время завершения заказа.
def update_order_complete_time(order_id, complete_time):
    with sql_connection() as local_con:
        cur = local_con.cursor()
        cur.execute('UPDATE orders SET end = ?, completed = true WHERE order_id = ?',
                    (complete_time, order_id))
        local_con.commit()


# Изменяет исполнителей заказа.
def update_order_executor(courier_info_dict, courier_type, order):
    with sql_connection() as local_con:
        cur = local_con.cursor()
        cur.execute('UPDATE orders SET executing_courier_id = ?, courier_type = ? WHERE '
                    'order_id = ?', (courier_info_dict['courier_id'], courier_type,
                                     order['order_id']))
        local_con.commit()


# Устанавливает время начала заказа.
def set_start_time(match_orders, assign_time):
    with sql_connection() as local_connection:
        cur = local_connection.cursor()
        for order_dict in match_orders:
            cur.execute('UPDATE orders SET start = ? WHERE order_id = ?',
                        (assign_time, order_dict['id']))
        local_connection.commit()


# Проверяем подходит ли заказ курьеру.
def check_order(order, regions, courier_hours_minutes_list, match_orders, courier_info_dict, courier_type):
    # Проверяем, что регион заказа есть в списке регионов курьера.
    if order['region'] in regions:
        # Считываем интервалы заказа.
        order_time_intervals = list(map(str, order['delivery_hours'].split()))
        # Преобразуем интервалы заказов.
        order_hours_minutes_list = help_functions.time_list(order_time_intervals)
        is_normal = False
        # Проходимся по списку интервалов курьера.
        for i in range(0, len(courier_hours_minutes_list), 2):
            # Считываем часы и минуты начала и конца работы курьера.
            left_hour = courier_hours_minutes_list[i][0]
            left_min = courier_hours_minutes_list[i][1]
            right_hour = courier_hours_minutes_list[i + 1][0]
            right_min = courier_hours_minutes_list[i + 1][1]
            was_added = False
            # Проходимся по списку интервалов заказа.
            for j in range(0, len(order_hours_minutes_list), 2):
                # Считываем часы и минуты начала и конца заказа.
                order_left_hour = order_hours_minutes_list[j][0]
                order_left_min = order_hours_minutes_list[j][1]
                order_right_hour = order_hours_minutes_list[j + 1][0]
                order_right_min = order_hours_minutes_list[j + 1][1]
                # Проверяем подходят ли часы доставки графику работы.
                if ((left_hour == right_hour == order_left_hour == order_right_hour and
                     (left_min < order_left_min < right_min or order_left_min < left_min < order_right_min or
                      left_min == order_left_min or order_right_min == right_min)) or
                        left_hour <= order_left_hour <= right_hour or order_left_hour <= left_hour <= order_right_hour):
                    match_orders.append({'id': order['order_id']})
                    update_order_executor(courier_info_dict, courier_type, order)
                    was_added = True
                    is_normal = True
                    break
                if was_added:
                    break
            if is_normal:
                break


# Проверяет, подходит ли заказ под параметры курьера.
def normal_order(order, regions, max_weight, courier_hours_minutes_list):
    # Изначально заказ не подходит.
    is_matching = False
    # Проверяем, что регион заказа есть в списке регионов курьера и вес не превышает грузоподъёмность.
    if order['region'] in regions and order['weight'] <= max_weight:
        # Считываем интервал заказа.
        order_time_intervals = list(map(str, order['delivery_hours'].split()))
        # Получаем список часов и минут начала и конца.
        order_hours_minutes_list = help_functions.time_list(order_time_intervals)
        # Проходимся по списку интервалов курьера, шаг 2, потому что часы и минуты - отдельные элементы списка.
        for i in range(0, len(courier_hours_minutes_list), 2):
            # Считываем начальные и конечные часы и минуты работы курьера.
            left_hour = courier_hours_minutes_list[i][0]
            left_min = courier_hours_minutes_list[i][1]
            right_hour = courier_hours_minutes_list[i + 1][0]
            right_min = courier_hours_minutes_list[i + 1][1]
            was_added = False
            # Проходимся по списку интервалов заказа, шаг 2, потому что часы и минуты - отдельные элементы списка.
            for j in range(0, len(order_hours_minutes_list), 2):
                # Считываем начальные и конечные часы и минуты доставки заказа.
                order_left_hour = order_hours_minutes_list[j][0]
                order_left_min = order_hours_minutes_list[j][1]
                order_right_hour = order_hours_minutes_list[j + 1][0]
                order_right_min = order_hours_minutes_list[j + 1][1]
                # Проверяем подходит ли время доставки под график курьера и если подходит, меняем значения флагов.
                if ((left_hour == right_hour == order_left_hour == order_right_hour and
                     (left_min < order_left_min < right_min or order_left_min < left_min < order_right_min or
                      left_min == order_left_min or order_right_min == right_min)) or
                        left_hour <= order_left_hour <= right_hour or order_left_hour <= left_hour <= order_right_hour):
                    was_added = True
                    is_matching = True
                    break
                if was_added:
                    break
            if is_matching:
                return is_matching
    return is_matching
