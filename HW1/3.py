def check_for_bites(value):
    try:
        bytes_value = eval(f'b"{value}"')
        print(f'Слово "{value}" возможно представить в байтовом типе - {bytes_value}')
    except SyntaxError:
        print("\033[31m{}\033[0m".format(f'Слово "{value}" не возможно представить в байтовом виде!'))


words_for_check = ('класс', 'attribute', 'type', 'функция',)
for i in words_for_check:
    check_for_bites(i)
