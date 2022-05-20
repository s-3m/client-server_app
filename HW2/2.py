import json


def write_order_to_json(item, quatity, price, buyer, date):
    order_dict = {
        'товар': item,
        'Количество': quatity,
        'Цена': price,
        'Покупатель': buyer,
        'Дата': date
    }
    with open('orders.json', 'r+', encoding='utf-8') as file:
        order = json.load(file)
        file.seek(0)
        order['orders'].append(order_dict)
        json.dump(order, file, indent=4, ensure_ascii=False)


write_order_to_json('Стул', '5', '500', 'Some buyer', '23-10-2022')
