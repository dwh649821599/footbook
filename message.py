import re


class Message(object):
    def __init__(self, name_list, format_):
        self.name_list = name_list
        self.format = format_

    def encode(self, *args):
        text = re.sub('\([^(]*\)', '{}', self.format).replace('\\', '')
        for i in range(len(args)):
            text = text.replace('{}', args[i], 1)
        return text

    def decode(self, text):
        res = re.match(self.format, text)
        if res:
            return {self.name_list[i]: res.group(i + 1) for i in range(len(self.name_list))}
        else:
            return {}

    def get_header_bin(self, message, sep):
        index = 0
        number = len(self.name_list) - 1
        while number > 0 and index < len(message):
            if message[index] == ord(sep):
                number -= 1
            index += 1
        dic = self.decode(message[:index].decode())
        dic[self.name_list[-1]] = message[index:]
        return dic



if __name__ == "__main__":
    m = Message(['sent_from', 'send_to', 'timestamp', 'index', 'all', 'text'],
                '([0-9]*)\$([0-9]*)\$([0-9]*)\$([0-9]*)\$([0-9]*)\$(.*)')
    '''print(m.decode(r'192.168.1.1$192.168.1.2$3333$4$8985$$$textwoshinidie$$$$dsajdhasjdsa$$$$'))
    m3 = Message(['ip', 'port', 'account', 'password'],
                 '([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\$([0-9]*)\$([0-9]*)\$([0-9]*)')
    print(m3.decode(r'3.1.233.31$4214214$214124214$314124214'))
    print(r'3.1.233.31$4214214$214124214$314124214')
    print(m.encode('233', '666', 'wdnmd', 'cnm', 'nmsl', 'dfdfasdfas'))
    print(m.decode(m.encode('233.1.1.1', '666.1.1.1', '111', '111', '111', 'dfdfasdfas')))'''
    print(m.get_header_bin(b'1$1$1$1$1$text', b'$'))
