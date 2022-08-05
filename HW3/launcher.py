import subprocess

process = []

while True:
    action = input(
        '-----------------------\n'
        'Что хотите сделать?\n p - запустить месенджер\n q - выйти\n x - завершить все процессы \n'
        '-----------------------\n')

    if action == 'q':
        break
    elif action == 'p':
        clients_count = int(input('Сколько клиентов создать?'))
        process.append(subprocess.Popen('python server.py', creationflags=subprocess.CREATE_NEW_CONSOLE))
        for i in range(clients_count):
            process.append(subprocess.Popen(f'python client_read.py -n TestUser{i+1}', creationflags=subprocess.CREATE_NEW_CONSOLE))
    elif action == 'x':
        while process:
            process.pop().kill()
