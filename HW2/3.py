import yaml

data_for_write = {
    'list': ['2€', '3€', '4€'],
    'number': '5€',
    'dict': {'first': '5€', 'second': '7€'}
}

with open('file.yaml', 'w+', encoding='utf-8') as file:
    yaml.dump(data_for_write, file, default_style=False, allow_unicode=True)
    file.seek(0)
    yaml_file = yaml.full_load(file)

if data_for_write == yaml_file:
    print('Ура, они одинаковые!!!')
else:
    print('Что-то не так. Файлы не совпадают.')
