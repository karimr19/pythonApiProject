import datetime
import json
import help_functions
import dateutil
import dateutil.parser
from flask import Flask, request, make_response
import DB

app = Flask(__name__)


# Обрабатывает запрос добавить курьеров в таблицу курьеров.
@app.route('/couriers', methods=['POST'])
def add_couriers():
    incorrect_couriers = []
    # Список значкний нового курьера.
    entities_list = []
    # Считываем тело запроса.
    input_json = request.json
    # Получаем данные из тела запроса.
    dicts_list = input_json['data']
    for i in range(len(dicts_list)):
        # Валидируем ключи словаря курьера.
        if ('courier_id' in dicts_list[i] and 'courier_type' in dicts_list[i] and
                'regions' in dicts_list[i] and 'working_hours' in dicts_list[i] and
                len(dicts_list[i]) == 4 and not DB.courier_exists(dicts_list[i]['courier_id']) and
                help_functions.validate_courier_input_type(dicts_list[i])):
            # Добавляем полученные данные.
            entities_list.append((dicts_list[i]['courier_id'], dicts_list[i]['courier_type'],
                                  help_functions.list_to_string(dicts_list[i]['regions']),
                                  help_functions.list_to_string(dicts_list[i]['working_hours'])))
        else:
            # Добавляем id курьерами с некорректными входными данными.
            incorrect_couriers.append({'id': dicts_list[i]['courier_id']})
    # Проверяем, были ли добавлены некорректные курьеры и формируем ответ.
    if len(incorrect_couriers) > 0:
        incorrect_output_dict = {'validation_error': {'couriers': incorrect_couriers}}
        response = app.response_class(response=json.dumps(incorrect_output_dict), status=400)
        return response
    else:
        correct_couriers = list()
        for i in range(len(dicts_list)):
            # Записываем информацию в таблицу курьеров.
            DB.insert_couriers(entities_list[i])
            # Добавляем id корректных курьеров в список.
            correct_couriers.append({'id': dicts_list[i]['courier_id']})
        correct_output_dict = {'couriers': correct_couriers}
        response = app.response_class(response=json.dumps(correct_output_dict), status=201)
        return response


# Обрабатывает запрос изменить данные курьера.
@app.route('/couriers/<int:courier_id>', methods=['PATCH'])
def edit_courier(courier_id):
    input_json = request.json
    # Проверяем существование курьера с заданным id и наличие ключей в теле запроса.
    if not DB.courier_exists(courier_id) or len(input_json) == 0 or \
            not(help_functions.validate_courier_edit(input_json)):
        return make_response("<h2>HTTP 400 Bad Request</h2>", 400)
    # Проходимся по всем ключам словаря и проверяем что они соответствуют ключам таблицы.
    for key in input_json:
        if key != 'courier_type' and key != 'regions' and key != 'working_hours':
            return make_response("<h2>HTTP 400 Bad Request</h2>", 400)
    # Изменяем таблицу курьеров.
    for key in input_json:
        DB.couriers_table_update(courier_id, key, input_json[key])
    # Изменяем таблицу заказов, если необходимо.
    DB.orders_table_update(courier_id)
    response = app.response_class(response=json.dumps(DB.courier_info(courier_id)), status=200)
    return response


# Обрабатывает запрос завершить заказ.
@app.route('/orders/complete', methods=['POST'])
def complete_order():
    input_dict = request.json
    # Проверяем корректность ключей, переданных в теле запроса.
    if 'courier_id' in input_dict and 'order_id' in input_dict and 'complete_time' in input_dict and \
            len(input_dict) == 3:
        courier_id = input_dict['courier_id']
        order_id = input_dict['order_id']
        # Проверяем корректность введенных id курьера и id заказа.
        if DB.courier_exists(courier_id) and DB.order_exists(order_id):
            complete_time = input_dict['complete_time']
            if DB.validate_order(order_id, courier_id, complete_time):
                DB.update_order_complete_time(order_id, complete_time)
                return make_response({'order_id': order_id}, 200)
    return make_response('<h2>HTTP 400 Bad Request</h2>', 400)


# Обрабатывает запрос добавить заказы в таблицу заказов.
@app.route('/orders', methods=['POST'])
def add_orders():
    incorrect_orders = []
    entities_list = []
    input_json = request.json
    dicts_list = input_json['data']
    # Проходимся по списку словарей и добавляем корректные словари.
    for i in range(len(dicts_list)):
        # Проверяем корректность ключей и значений.
        if ('order_id' in dicts_list[i] and 'weight' in dicts_list[i] and
                'region' in dicts_list[i] and 'delivery_hours' in dicts_list[i] and len(dicts_list[i]) == 4 and
                0.01 <= dicts_list[i]['weight'] <= 50 and not DB.order_exists(dicts_list[i]['order_id']) and
                help_functions.validate_order_input_type(dicts_list[i])):
            entities_list.append((dicts_list[i]['order_id'], dicts_list[i]['weight'], dicts_list[i]['region'],
                                  help_functions.list_to_string(dicts_list[i]['delivery_hours'])))
        else:
            incorrect_orders.append({'id': dicts_list[i]['order_id']})
    # Проверяем были ли найдены некорректные заказы.
    if len(incorrect_orders) > 0:
        incorrect_output_dict = {'validation_error': {'orders': incorrect_orders}}
        response = app.response_class(response=json.dumps(incorrect_output_dict), status=400)
        return response
    else:
        correct_orders = list()
        # Проходимся по всем корректным заказам.
        for i in range(len(dicts_list)):
            # Добавляем заказы в таблицу.
            DB.insert_orders(entities_list[i])
            # Добавляем id заказов в список для вывода.
            correct_orders.append({'id': dicts_list[i]['order_id']})
        correct_output_dict = {'orders': correct_orders}
        response = app.response_class(response=json.dumps(correct_output_dict), status=201)
        return response


# Обрабатывает запрос получить информацию о курьере.
@app.route('/couriers/<int:courier_id>', methods=['GET'])
def give_courier_info(courier_id):
    # Проверяем существование курьера в таблице.
    if DB.courier_exists(courier_id):
        # Читаем информацию о курьере.
        courier_dict = DB.courier_info(courier_id)
        # Получаем список заказов, которые назначены данному курьеру.
        orders_list = DB.orders_info(int(courier_dict['courier_id']))
        # Для подсчета заработка курьера.
        earnings = 0
        # Выводим рейтинг, если курьер развез хотя бы 1 заказ
        if len(orders_list) > 0:
            # Словарь, в который будем добавлять время доставки по району.
            region_dict = {}
            # Заполняем словарь ключами-регионами.
            for order in orders_list:
                if not order['region'] in region_dict:
                    region_dict[order['region']] = []
            # Проходимся по каждому заказу и добавляем значения в словарь.
            for order in orders_list:
                # Время начала заказа.
                start_time = dateutil.parser.isoparse(order['start'])
                # Время конца заказа.
                end_time = dateutil.parser.isoparse(order['end'])
                # Время доставки в секундах.
                time_delta = round((end_time - start_time).total_seconds())
                # Добавляем время доставки в соответствующий регион.
                region_dict[order['region']].append(time_delta)
                # Увеличиваем заработок курьера с учетом типа курьера на момент назначения заказа.
                earnings += salary_dict[order['courier_type']] * 500
            # Считаем рейтинг курьера.
            rating = help_functions.count_rating(region_dict)
            # Читаем информацию о курьере для вывода.
            courier_dict = DB.courier_info(courier_id)
            courier_dict['rating'] = round(rating, 2)
            courier_dict['earnings'] = earnings
            response = app.response_class(response=json.dumps(courier_dict), status=200)
            return response
        # Выводим информацию без рейтинга если нет выполненных заказов.
        else:
            # Читаем информацию о курьере для вывода.
            courier_dict = DB.courier_info(courier_id)
            courier_dict['earnings'] = 0
            response = app.response_class(response=json.dumps(courier_dict), status=200)
            return response
    return make_response('<h2>HTTP 400 Bad Request</h2>', 400)


# Обрабатывает запрос назначения заказов.
@app.route('/orders/assign', methods=['POST'])
def assign_courier():
    input_json = request.json
    # Проверяем корректность id курьера.
    if not ('courier_id' in input_json and len(input_json) == 1) or not DB.courier_exists(input_json['courier_id']):
        return make_response('<h2>HTTP 400 Bad Request</h2>', 400)
    # Читаем информацию о курьере.
    courier_info_dict = DB.courier_info(input_json['courier_id'])
    match_orders = []
    # Проверяем, что рабочие часы и регионы работы не пустые.
    if courier_info_dict['working_hours'] != '' and courier_info_dict['regions'] != '':
        time_intervals = list(map(str, courier_info_dict['working_hours'].split()))
        courier_hours_minutes_list = help_functions.time_list(time_intervals)
        # Регионы где работает курьер.
        regions = list(map(int, courier_info_dict['regions'].split()))
        # Смотрим грузоподьёмность курьера.
        max_weight = DB.weight_dict[courier_info_dict['courier_type']]
        # Смотрим тип курьера для расчета зарплаты.
        courier_type = courier_info_dict['courier_type']
        orders_info_list = DB.orders_to_assign(max_weight)
        # Проверяем, нашлись ли заказы.
        if len(orders_info_list) != 0:
            # Проходим по всем заказам.
            for order in orders_info_list:
                # Проверяем подходят ли они.
                DB.check_order(order, regions, courier_hours_minutes_list, match_orders, courier_info_dict,
                               courier_type)
        # Проверяем были ли добавлены подходящие заказы.
        if len(match_orders) != 0:
            # Вычисляем нынешнее время +00:00
            d = datetime.datetime.utcnow()
            # Время по Зулу
            assign_time = str(d.isoformat("T"))[:-4] + 'Z'
            # Устанавливаем время начала заказов.
            DB.set_start_time(match_orders, assign_time)
            response = app.response_class(response=json.dumps({'orders': match_orders, 'assign_time': assign_time}),
                                          status=201)
            return response
    response = app.response_class(response=json.dumps({'orders': match_orders}), status=201)
    return response


# Словарь для перевода типа курьера в коэффициент зарплаты.
salary_dict = {'foot': 2, 'bike': 5, 'car': 9}
# Устанавливаем соединение с бд.
con = DB.sql_connection()
# Создаем таблицу курьеров.
DB.create_couriers_table()
# Создаем таблицу заказов.
DB.create_orders_table()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
