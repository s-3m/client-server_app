def str_byte_transform(val):
    print(f'Преобразуем аргумент "{val}"')
    val = val.encode('utf-8')
    print(f'В байтовом виде - {val}')
    val = val.decode('utf-8')
    print(f'В виде строки - {val}')


words_for_check = ('разработка', 'администрирование', 'protocol', 'standart')

for i in words_for_check:
    str_byte_transform(i)
