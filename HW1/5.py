import subprocess
import chardet
import platform


def ping_url(url):
    print(f'{"*"*15} Start ping "{url}" {"*"*15}')
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    args = ['ping', param, '2', url]
    process = subprocess.Popen(args, stdout=subprocess.PIPE)
    for line in process.stdout:
        result = chardet.detect(line)
        print(line.decode(result['encoding']).encode('utf-8').decode('utf-8'))


urls_list = ['yandex.ru', 'youtube.com']
for i in urls_list:
    ping_url(i)
