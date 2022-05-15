import chardet

with open('test_file.txt', 'w') as file:
    file.write('сетевое программирование\nсокет\nдекоратор')

# Всплыло два решения, не знаю какое из них наиболее верное, оставляю оба!

# ---------------------------------ВАРИАНТ 1-------------------------

file = open('test_file.txt', 'rb')
result = chardet.detect(file.read())['encoding']
with open('test_file.txt', 'r', encoding=result) as file:
    print(file.read())

print('\n', 'Вариант № 2', '\n')
# ---------------------------------ВАРИАНТ 2-------------------------

with open('test_file.txt', 'r') as file:
    print(file.read().encode('utf-8').decode('utf-8'))
