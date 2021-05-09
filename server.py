import asyncio
import socket
import message
import time
import threading
import pickle
import datetime
import Operator

# 服务端IP地址与端口号
TCP_HOST = ('0.0.0.0', 49999)
UDP_HOST = ('0.0.0.0', 10000)
UDP_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
UDP_SOCKET.bind(UDP_HOST)
# 用户在线状态以及本次在线所使用的端口
USER = {}
for i in Operator.get_all_users():
    USER[i[0]] = ''

GROUP = Operator.get_all_groups()

temp = {}

# 用户消息缓存
MSG_BUFFER = {}
for i in Operator.get_all_users():
    MSG_BUFFER[i[0]] = []
# MSG_BUFFER = {1: [], 2: [], 3: [], 4: [], 5: [], 662970425: [], 692370170: []}

BUF = []

USER_KEY = ['id', 'psw']
USER_VALUE = '([0-9]*)\$([0-9A-Za-z]*)'

MSG_KEY = ['source', 'dest', 'timestamp', 'type', 'text']
MSG_VALUE = '([0-9]*)\$([0-9]*)\$([0-9\.]*)\$([0-9])\$(.*)'


class ServerProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        threading.Thread(target=self.check_buf).start()

    def check_buf(self):
        while True:
            if BUF:
                data, addr = BUF.pop(0)
                # 有用户上线
                try:
                    data.decode()
                except:
                    pass
                else:
                    if data.decode().startswith('UDP request from'):
                        user_id = int(data.decode()[len('UDP request from '):])
                        USER[user_id] = addr
                        # MSG_BUFFER[int(data.decode()len[('UDP request from')]:)] = []
                        # print(addr)
                        # 发送缓存消息
                        # print(MSG_BUFFER)
                        if MSG_BUFFER[user_id]:
                            for i in MSG_BUFFER[user_id]:
                                # time.sleep(0.5)
                                # print('send', i.decode(), 'to', addr)
                                self.transport.sendto(i, addr)
                        # print(MSG_BUFFER)
                        MSG_BUFFER[user_id] = []
                        continue
                # 在线用户发送消息
                msg = message.Message(MSG_KEY, MSG_VALUE)
                msg_dir = msg.get_header_bin(data, b'$')

                source = int(msg_dir['source'])
                dest = int(msg_dir['dest'])
                timestamp = float(msg_dir['timestamp'])
                datetime_str = datetime.datetime.strftime(datetime.datetime.fromtimestamp(timestamp),
                                                          '%Y-%m-%d %H:%M:%S.%f')
                msg_type = int(msg_dir['type'])
                msg_text = msg_dir['text']

                # print('user:' + str(USER))
                # print(MSG_BUFFER)
                # print(USER)
                if msg_type == 4:
                    if msg_text == b'get_user_info':
                        if int(dest) in USER.keys() and USER[int(dest)] != '':
                            optus = Operator.User()
                            optus.existence(source)
                            m = msg.encode(str(source), str(dest), str(timestamp), '4',
                                           'get_user_info').encode() + pickle.dumps(
                                optus.getinfo())
                            self.transport.sendto(m, addr)
                    if msg_text == b'audio_request' or msg_text == b'audio_accept' or msg_text == b'video_request' or msg_text == b'video_accept':
                        if int(dest) in USER.keys() and USER[int(dest)] != '':
                            self.transport.sendto(data, (USER[int(dest)][0], USER[int(dest)][1]))
                    if msg_text[:11] == b'modify_head':
                        optus = Operator.User()
                        optus.existence(source)
                        optus.modify_head(pickle.loads(msg_text[11:]))
                        print(f'{source}修改头像成功')
                    if msg_text == b'search_friend':
                        optus = Operator.User()
                        if optus.existence(dest) != 'Error':
                            print(f'查找到用户{dest}')
                            m = msg.encode(str(dest), str(source), str(timestamp), '4',
                                           'search_friend_OK').encode() + pickle.dumps(
                                {'id': optus.id, 'name': optus.name, 'head': optus.head})
                            self.transport.sendto(m, addr)
                        else:
                            print(f'未查找到用户{dest}')
                            m = msg.encode(str(dest), str(source), str(timestamp), '4', 'search_friend_NO').encode()
                            self.transport.sendto(m, addr)
                    if msg_text == b'add_friend_request':
                        if int(dest) in USER.keys() and USER[int(dest)] != '':
                            print(f'{source}想把{dest}加为好友')
                            optus = Operator.User()
                            optus.existence(source)
                            m = msg.encode(str(source), str(dest), str(timestamp), '4',
                                           'add_friend_request').encode() + pickle.dumps(
                                {'id': optus.id, 'name': optus.name, 'head': optus.head})
                            self.transport.sendto(m, (USER[int(dest)][0], USER[int(dest)][1]))
                        else:
                            print(f'{dest}不在线')
                    if msg_text == b'add_friend_accept':
                        if int(dest) in USER.keys() and USER[int(dest)] != '':
                            optus = Operator.User()
                            optus.existence(source)
                            ok = optus.add_friends(int(dest))
                            if str(ok) == 'OK':
                                print(f'{source}同意添加{dest}为好友')
                                self.transport.sendto(data, (USER[int(dest)][0], USER[int(dest)][1]))
                            else:
                                print(f'{source}和{dest}已经是好友')
                        else:
                            print(f'{dest}不在线')
                    if msg_text == b'online/offline':
                        if int(dest) in USER.keys() and USER[int(dest)] != '':
                            m = msg.encode(str(source), str(dest), str(timestamp), '4',
                                           'online/offline online').encode()
                            self.transport.sendto(m, addr)
                        else:
                            m = msg.encode(str(source), str(dest), str(timestamp), '4',
                                           'online/offline offline').encode()
                            self.transport.sendto(m, addr)
                    continue

                if msg_text == b'':
                    continue

                else:
                    # 消息记录入库
                    if msg_type == 0:
                        optus = Operator.User()
                        optus.existence(source)
                        optus.say_message(dest, time=datetime_str, content=data)

                    # 如果用户在线并且该用户存在，转发消息
                    if int(dest) in USER.keys() and USER[int(dest)] != '':
                        time.sleep(0.000001)
                        self.transport.sendto(data, (USER[int(dest)][0], USER[int(dest)][1]))
                        # 回送
                        m = msg.encode(str(source), str(source), str(timestamp), '9999', '1').encode()
                        self.transport.sendto(m, addr)
                    # print(str(n))
                    # self.transport.sendto(dest_addr.encode(), (USER[int(source)][0], USER[int(source)][1]))
                    # 否则存储
                    else:
                        if msg_type == 0:
                            # print(f"{dest}不在线")
                            MSG_BUFFER[int(dest)].append(data)
                # print('msg_buffer:' + str(MSG_BUFFER))
                # self.transport.sendto(data, addr)

    def datagram_received(self, data, addr):
        # 消息入队列
        BUF.append((data, addr))
        # print(len(BUF))

    def pause_writing(self):
        pass

    def resume_writing(self):
        pass

    def connection_lost(self, exc):
        print('udp连接关闭', exc)
        # self.transport.close()


async def tcp_connect(reader, writer):
    # 接受不同TCP客户端的连接
    while True:
        try:
            data = await reader.read(65535)
        except ConnectionResetError as e:
            addr = writer.get_extra_info('peername')
            print('TCP连接错误', e)
            writer.close()
            print(f"客户端被终止,与{addr}的TCP连接关闭")
            for _i in USER.keys():
                if USER[_i] != '' and addr[0] == USER[_i][0]:
                    USER[_i] = ''
                    break
            break
        addr = writer.get_extra_info('peername')
        if not data:
            print(f"与{addr}的TCP连接关闭")
            for _i in USER.keys():
                if addr[0] == USER[_i][0]:
                    USER[_i] = ''
                    break
            writer.close()
            await writer.wait_closed()
            break
        # 注册
        # print(data)
        if data[0] == 36:  # $
            info = pickle.loads(data[1:])
            optus = Operator.User()
            id = optus.register(info['id'], info['name'], info['password'], info['sex'], info['address'],
                                info['hometown'], info['occupation'], info['birthday'], info['introduction'],
                                info['head'])
            print(id)
            if id == '重复' or id == -1:
                print('注册失败')
                writer.write('failed '.encode())
                break
            else:
                USER[id] = ''
                MSG_BUFFER[int(id)] = []
                print('注册成功')
                writer.write('succeed '.encode())
                break

        msg = message.Message(USER_KEY, USER_VALUE)
        msg_dict = msg.decode(data.decode('utf-8'))

        user_id = int(msg_dict['id'])
        user_psw = msg_dict['psw']

        print(f"用户{user_id}在{addr}上请求登陆")
        USER[user_id] = ''

        optus = Operator.User()
        isexistence = optus.existence(user_id)

        if not optus.login(user_psw) or isexistence == 'Error':
            writer.write('refuse '.encode())
            await writer.drain()
            print(f"{user_id}不存在或密码错误,TCP连接关闭")
            writer.close()
            await writer.wait_closed()
            USER[user_id] = ''
            break
        else:
            writer.write('access '.encode())
            user_infolist = optus.getinfo()
            infolist = pickle.dumps(user_infolist) + b'$ff$ff$ff$'
            writer.write(infolist)


async def main():
    # 创建UDP套接字,所有用户共同使用
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: ServerProtocol(),
        sock=UDP_SOCKET
    )

    server = await asyncio.start_server(tcp_connect, TCP_HOST[0], TCP_HOST[1])

    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())
