
import pickle
import asyncio

from . import message
from .protocol import EchoClientProtocol

LOCAL_IP = '172.22.216.94'
LOCAL_PORT = 9999
try:
    with open('ipconfig', 'r') as f:
        REMOTE_IP = f.readline().strip()
        REMOTE_TCP_PORT = int(f.readline().strip())
        REMOTE_UDP_PORT = int(f.readline())
except Exception as e:
    print(e)
    REMOTE_IP = '118.202.40.86'
    REMOTE_TCP_PORT = 49999
    REMOTE_UDP_PORT = 10000

print(REMOTE_IP, REMOTE_TCP_PORT)

SEND_ID = '456'

TCP_MESSAGE_FORMAT = message.Message(['account', 'password'],
                                     '([0-9]*)\$([0-9A-Za-z]*)')
UDP_MESSAGE_FORMAT = message.Message(['sent_from', 'send_to', 'timestamp', 'type', 'text'],
                                     '([0-9]*)\$([0-9]*)\$([0-9\.]*)\$([0-9])\$(.*)')


class ClientNetwork(object):
    def __init__(self, user_id, user_psw):
        self.user_id = user_id
        self.user_psw = user_psw
        self.reader = None
        self.writer = None
        self.init_personal_info = None

    async def tcp_connect(self, message):
        # 如连不上服务器，抛出ConnectionRefusedError
        try:
            self.reader, self.writer = await asyncio.open_connection(
                REMOTE_IP, REMOTE_TCP_PORT)
        except ConnectionRefusedError:
            raise ConnectionRefusedError('连不上服务器')

        # 注册
        # print(message[0])
        if message[0] == 36:  # b'$':
            # print(f'Send: {message!r}')
            self.writer.write(message)
            data = await self.reader.readuntil(b' ')    # succeed or failed
            # print(data)
            return True if data.decode() == 'succeed ' else False

        # print(f'Send: {message!r}')
        self.writer.write(message.encode())
        try:
            data = await self.reader.readuntil(b' ')  # access or refuse
            if data.decode() == 'access ':
                self.init_personal_info = await self.reader.readuntil(b'$ff$ff$ff$')  # personal_info
                self.init_personal_info = pickle.loads(self.init_personal_info[:-10])
        except Exception as e:
            print(e)
            raise ConnectionError('没有收到服务器返回或服务器返回格式错误')
        print(f'Received: {data.decode()!r}')
        # print('info ', self.init_personal_info)

        return True if data.decode() == 'access ' else False

    async def tcp_disconnect(self):
        print('Close the connection')
        self.writer.close()
        # await self.writer.wait_closed()
        self.writer = None

    async def udp_connect(self, **kwargs):
        loop = asyncio.get_running_loop()

        on_con_lost = loop.create_future()

        transport, protocol = await loop.create_datagram_endpoint(
            lambda: EchoClientProtocol(self.user_id,
                                       'UDP request from {}'.format(self.user_id),  on_con_lost, **kwargs),
            remote_addr=(REMOTE_IP, REMOTE_UDP_PORT))

        try:
            await on_con_lost
        finally:
            transport.close()



async def main(id, psw):
    USER_ID = id#'123'
    USER_PSW = psw#'123'
    c = ClientNetwork(USER_ID, USER_PSW)
    if await c.tcp_connect(TCP_MESSAGE_FORMAT.encode(USER_ID, USER_PSW)):
        await c.udp_connect()
    await c.tcp_disconnect()


async def m():
    loop = asyncio.get_event_loop()
    '''for i in range(1, 2):
        await asyncio.sleep(0.05)
        loop.create_task(main(str(i), str(i)))'''
    await asyncio.sleep(0.05)
    loop.create_task(main(str(8434023), str(123456)))
    await asyncio.sleep(0.5)
    loop.create_task(main(str(84340214), str(123456)))

if __name__ == '__main__':
    # asyncio.run(tcp_echo_client(TCP_MESSAGE_FORMAT.encode(USER_ID, USER_PSW)))
    loop = asyncio.get_event_loop()
    # loop.create_task(f())
    loop.create_task(m())

    loop.run_forever()

