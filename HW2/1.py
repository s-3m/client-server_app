import chardet
import re
import csv
import glob


def get_coding(file_name):
    with open(file_name, 'rb') as file:
        return chardet.detect(file.read())['encoding']


def get_data():
    file_list = glob.glob('*.txt')
    os_prod_list, os_name_list, os_code_list, os_type_list = [], [], [], []
    main_data = [['Изготовитель системы', 'Название ОС', 'Код продукта', 'Тип системы']]
    for file in file_list:
        with open(file, 'r', encoding=get_coding(file)) as f:
            ready_file = f.read()
            item_os_prod = re.search(r'Изготовитель системы:\s+(\b\w+)', ready_file)
            os_prod_list.append(item_os_prod[1])
            item_os_name = re.search(r'Название ОС:\s+\w+\s(\w+\s\d+)', ready_file)
            os_name_list.append(item_os_name[1])
            item_os_code = re.search(r'Код продукта:\s+(\S+)', ready_file)
            os_code_list.append(item_os_code[1])
            item_os_type = re.search(r'Тип системы:\s+(\S+)', ready_file)
            os_type_list.append(item_os_type[1])
    zip_value = zip(os_prod_list, os_name_list, os_code_list, os_type_list)
    for i in zip_value:
        main_data.append(list(i))
    return main_data


def write_to_csv(link):
    print(get_data())
    with open(link, 'w', encoding='utf-8') as file:
        file_writer = csv.writer(file)
        file_writer.writerows(get_data())


write_to_csv('my_csv.csv')

