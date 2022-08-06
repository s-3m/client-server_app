class ServerPortChecker:

    def __set__(self, instance, value):
        if int(float(value)) < 0 or not str(value).isdigit():
            print('Номер порта должен быть целым положительным числом\nУстановлен порт по умолчанию - 7777')
            value = 7777
        instance.__dict__[self.name] = int(value)

    def __set_name__(self, owner, name):
        self.name = name
