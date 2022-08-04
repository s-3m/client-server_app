import platform
from subprocess import Popen, PIPE
import threading
from ipaddress import ip_address
import tabulate


res = []


def host_ping(hosts_list, flag=False):
    if not isinstance(hosts_list, list):
        hosts_list = [hosts_list]
    for ip in hosts_list:
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '1', ip]
        process = Popen(command, stdout=PIPE, stderr=PIPE)
        answer = process.wait()
        if flag:
            if answer == 0:
                res.append({'Адрес доступен': ip})
            else:
                res.append({'Адрес недоступен': ip})

        else:
            if answer == 0:
                print(f'Узел {ip} доступен')
            else:
                print(f'Узел {ip} недоступен')


def host_range_ping(tab_print=False):
    while True:
        start_range = input('Введите начальный ip-адрес: ')
        try:
            arg = ip_address(start_range)
            break
        except ValueError:
            print('Вы ввели не цифровой ip-адрес.')

    while True:
        end_range = input('Сколько адресов проверить?: ')
        if int(end_range) <= 256:
            break
        else:
            print('Можем менять только последний октет')

    print('Начинаю проверку ip-адресов!')
    threads = []

    for i in range(int(end_range)+1):
        thread = threading.Thread(target=host_ping, args=(str(arg), True if tab_print else None,))
        thread.start()
        threads.append(thread)
        arg += 1

    for t in threads:
        t.join()


def host_range_ping_tab():
    host_range_ping(True)
    print(tabulate.tabulate(res, headers='keys', tablefmt='pipe', stralign='center'))


if __name__ == '__main__':
    host_range_ping_tab()
