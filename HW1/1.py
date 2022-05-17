def just_print(value):
    print(f'{type(i)} - {i}')


print('*' * 30, 'Для строк', '*' * 30)
words_tuple = ('разработка', 'сокет', 'декоратор')
for i in words_tuple:
    just_print(i)

print('*' * 30, 'Для кодовых точек', '*' * 30)

uni_development = '\u0440\u0430\u0437\u0440\u0430\u0431\u043e\u0442\u043a\u0430'
uni_socket = '\u0441\u043e\u043a\u0435\u0442'
uni_decorator = '\u0434\u0435\u043a\u043e\u0440\u0430\u0442\u043e\u0440'
for i in (uni_development, uni_socket, uni_decorator):
    just_print(i)
