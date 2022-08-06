import dis


class ClientVerifier(type):
    def __init__(cls, cls_name, cls_parent, cls_attrs):

        method = []
        method_2 = []
        attrs = []

        for func in cls_attrs:
            try:
                result = dis.get_instructions(cls_attrs[func])
            except TypeError:
                pass
            else:
                for i in result:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in method:
                            method.append(i.argval)
                    elif i.opname == 'LOAD_METHOD':
                        if i.argval not in method_2:
                            method_2.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in attrs:
                            attrs.append(i.argval)

        if 'accept' in method or 'listen' in method or 'socket' in method:
            raise TypeError('Использование методов ("accept", "listen", "soclet") не допустимо в клиентских классах!')
        elif 'get_message' in method or 'send_message' in method:
            pass
        else:
            TypeError('Отсутствуют функции, работающие с сокетами.')
        super().__init__(cls_name, cls_parent, cls_attrs)


class ServerVerifier(type):
    def __init__(cls, cls_name, cls_parent, cls_attrs):

        method = []
        method_2 = []
        attrs = []

        for func in cls_attrs:
            try:
                result = dis.get_instructions(cls_attrs[func])
            except TypeError:
                pass
            else:
                for i in result:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in method:
                            method.append(i.argval)
                    elif i.opname == 'LOAD_METHOD':
                        if i.argval not in method_2:
                            method_2.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in attrs:
                            attrs.append(i.argval)

        if 'connect' in method:
            raise TypeError('Использование методов: ("connect") - не допустимо в серверных классах!')
        elif 'AF_INET' not in attrs or 'SOCK_STREAM' not in attrs:
            raise TypeError('Неправильная инициализация сокетов.')
        super().__init__(cls_name, cls_parent, cls_attrs)
